"""
Configura webhook global UAZAPI após deploy no Render.

Uso:
  cd backend
  .venv\\Scripts\\activate
  python scripts/setup_global_webhook.py --url https://fit-api.onrender.com

Requer no .env: UAZAPI_ADMIN_TOKEN, WEBHOOK_SECRET
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND / ".env")

from core.config import get_settings
from core.uazapi_admin import get_uazapi_admin


def main() -> int:
    parser = argparse.ArgumentParser(description="Configura webhook global UAZAPI")
    parser.add_argument(
        "--url",
        required=True,
        help="URL base do Render, ex: https://fit-api-xxxx.onrender.com",
    )
    args = parser.parse_args()

    settings = get_settings()
    admin = get_uazapi_admin()

    if not admin.configured():
        print("ERRO: defina UAZAPI_BASE_URL e UAZAPI_ADMIN_TOKEN no backend/.env")
        return 1

    if not settings.webhook_secret:
        print("ERRO: defina WEBHOOK_SECRET no backend/.env")
        return 1

    base = args.url.rstrip("/")
    webhook_url = f"{base}/webhook/uazapi?wh={settings.webhook_secret}"

    print(f"Configurando webhook global:\n  {webhook_url}\n")

    result = admin.configure_global_webhook(webhook_url)
    print("OK:", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
