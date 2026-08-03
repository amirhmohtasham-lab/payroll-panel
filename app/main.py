"""FastAPI app factory — registers all routers, CORS, and startup hooks."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, fertilizer, greenhouse, reports, uploads
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Payroll Panel", version="3.0.0", docs_url=None, redoc_url=None)

if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(fertilizer.router)
app.include_router(reports.router)
app.include_router(chat.router)
app.include_router(greenhouse.router)


@app.get("/api/healthz")
def healthz():
    return {"ok": True}
