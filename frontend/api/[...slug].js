// Vercel serverless proxy — forwards /api/* to the Payroll Panel backend on the VPS.
// This lets the hosted frontend talk to the real backend WITHOUT Cloudflare/CORS:
//   browser → vercel.app/api/* (same origin) → this function → http://VPS:8766/api/*
export default function handler(req, res) {
  const { pathname, search } = new URL(req.url, 'http://localhost');
  const target = `http://103.83.86.141:8766${pathname}${search}`;

  const headers = { ...req.headers };
  headers['x-forwarded-proto'] = 'https'; // backend issues cross-site-friendly cookie
  delete headers.host;

  const options = { method: req.method, headers, duplex: 'half' };
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    options.body = req; // stream the request body (uploads) through
  }

  fetch(target, options)
    .then((upstream) => {
      res.statusCode = upstream.status;
      upstream.headers.forEach((value, key) => {
        if (key.toLowerCase() !== 'transfer-encoding') res.setHeader(key, value);
      });
      const reader = upstream.body.getReader();
      const pump = () =>
        reader.read().then(({ done, value }) => {
          if (done) {
            res.end();
            return;
          }
          res.write(Buffer.from(value));
          pump();
        });
      pump();
    })
    .catch((err) => {
      res.statusCode = 502;
      res.setHeader('Content-Type', 'text/plain; charset=utf-8');
      res.end('Proxy error: ' + err.message);
    });
}
