// Greenhouse (soil) — placeholder page (coming soon).

import { Layout } from '../components/Layout';
import { ACCOUNTANT_NAV } from '../lib/nav';
import { GhLeaf } from '../ui/icons';

export function SoilGreenhousePage() {
  return (
    <Layout title="گلخانه خاکی" navItems={ACCOUNTANT_NAV}>
      <section className="page-intro">
        <div>
          <span className="eyebrow">Greenhouse — Soil</span>
          <h2>گلخانه خاکی</h2>
          <p>تحلیل اقلیم و آمار گلخانه خاکی</p>
        </div>
        <span className="season-mark" style={{ fontSize: '2.2rem' }}><GhLeaf size={40} /></span>
      </section>
      <div className="card">
        <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem 0' }}>
          این بخش به‌زودی راه‌اندازی می‌شود.
        </p>
      </div>
    </Layout>
  );
}
