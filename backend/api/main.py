import sys
from pathlib import Path

from core.ssl_fix import apply_dev_ssl_patches, configure_ssl

configure_ssl()
apply_dev_ssl_patches()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Garante imports `core`, `agents` ao rodar de backend/
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.routes import attendance, health, webhook  # noqa: E402
from core.config import get_settings  # noqa: E402
from core.logging_setup import setup_logging, startup_banner  # noqa: E402

setup_logging()
settings = get_settings()
startup_banner(
    "FIT API",
    webhook="/webhook/uazapi",
    docs="/docs",
)

app = FastAPI(
    title="FIT Backend",
    description="Superagente para academias — WhatsApp + Agno + Mistral",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(attendance.router)


@app.get("/")
def root():
    return {
        "service": "fit-backend",
        "docs": "/docs",
        "health": "/health",
        "webhooks": [
            "/webhook/uazapi?wh=WEBHOOK_SECRET",
            "/api/whatsapp/webhook?wh=WEBHOOK_SECRET",
        ],
    }
