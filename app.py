"""
Entrypoint Render quando Root Directory não é `backend`.

Start: uvicorn app:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from api.main import app  # noqa: E402, F401

__all__ = ["app"]
