"""Fase 4 — check-in/out via QR (stub inicial)."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import get_settings
from core.supabase_client import get_supabase

router = APIRouter(prefix="/attendance", tags=["attendance"])


class CheckInRequest(BaseModel):
    token: str
    gym_id: str


@router.post("/check-in")
def check_in(body: CheckInRequest):
    """Valida token QR e registra presença."""
    settings = get_settings()
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()

    sb = get_supabase()
    row = (
        sb.table("qr_tokens")
        .select("*")
        .eq("gym_id", body.gym_id)
        .eq("token_hash", token_hash)
        .maybe_single()
        .execute()
    )
    if not row.data:
        raise HTTPException(400, "QR inválido")

    token = row.data
    if token.get("used_at"):
        raise HTTPException(400, "QR já utilizado")

    expires = datetime.fromisoformat(token["expires_at"].replace("Z", "+00:00"))
    if expires < datetime.now(timezone.utc):
        raise HTTPException(400, "QR expirado")

    sb.table("qr_tokens").update(
        {"used_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", token["id"]).execute()

    att = (
        sb.table("attendance")
        .insert(
            {
                "gym_id": body.gym_id,
                "member_id": token["member_id"],
                "source": "qr",
                "qr_token_id": token["id"],
            }
        )
        .execute()
    )

    return {"ok": True, "attendance_id": att.data[0]["id"], "member_id": token["member_id"]}


def generate_qr_token(gym_id: str, member_id: str, hours_valid: int = 4) -> str:
    """Gera token bruto para QR (uso interno agente/jobs)."""
    settings = get_settings()
    raw = secrets.token_urlsafe(32)
    signed = hmac.new(
        settings.qr_signing_secret.encode(),
        raw.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    token = f"{raw}.{signed}"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(hours=hours_valid)

    sb = get_supabase()
    sb.table("qr_tokens").insert(
        {
            "gym_id": gym_id,
            "member_id": member_id,
            "token_hash": token_hash,
            "expires_at": expires.isoformat(),
        }
    ).execute()
    return token
