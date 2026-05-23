"""Operações de banco usadas pelo webhook e pelas tools."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from core.supabase_client import get_supabase

TZ_BR = ZoneInfo("America/Sao_Paulo")


def get_gym_by_id(gym_id: str) -> dict[str, Any] | None:
    if not gym_id:
        return None
    sb = get_supabase()
    res = sb.table("gyms").select("*").eq("id", gym_id).maybe_single().execute()
    return res.data if res else None


def get_gym_by_slug(slug: str) -> dict[str, Any] | None:
    if not slug:
        return None
    sb = get_supabase()
    res = sb.table("gyms").select("*").eq("slug", slug).maybe_single().execute()
    return res.data if res else None


def resolve_gym_id(preferred_id: str | None = None, slug: str | None = None) -> str:
    """
    Resolve gym_id para AgentOS/dev: tenta UUID do .env, depois slug (piloto).
    """
    from core.config import get_settings

    settings = get_settings()
    candidates: list[str] = []
    if preferred_id:
        candidates.append(preferred_id.strip())
    if settings.default_gym_id:
        candidates.append(settings.default_gym_id.strip())

    seen: set[str] = set()
    for gid in candidates:
        if not gid or gid in seen:
            continue
        seen.add(gid)
        if get_gym_by_id(gid):
            return gid

    fallback_slug = (slug or settings.default_gym_slug or "piloto").strip()
    gym = get_gym_by_slug(fallback_slug)
    if gym:
        return gym["id"]

    raise RuntimeError(
        f"Academia não encontrada no Supabase. "
        f"Rode seed_piloto_completo.sql e defina DEFAULT_GYM_ID ou DEFAULT_GYM_SLUG={fallback_slug!r}."
    )


def gym_data_summary(gym_id: str) -> dict[str, int]:
    """Contagens rápidas para validar seed no startup."""
    sb = get_supabase()
    plans = (
        sb.table("plans")
        .select("id", count="exact")
        .eq("gym_id", gym_id)
        .eq("active", True)
        .execute()
    )
    slots = (
        sb.table("class_slots")
        .select("id", count="exact")
        .eq("gym_id", gym_id)
        .gte("starts_at", datetime.now(timezone.utc).isoformat())
        .execute()
    )
    members = (
        sb.table("members")
        .select("id", count="exact")
        .eq("gym_id", gym_id)
        .execute()
    )
    return {
        "planos": plans.count or 0,
        "horarios_futuros": slots.count or 0,
        "membros": members.count or 0,
    }


def resolve_gym_from_uazapi_instance(
    instance_id: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Webhook global: identifica academia pelo ID da instância UAZAPI.
    Retorna (gym, token_da_instância).
    """
    sb = get_supabase()

    inst = (
        sb.table("gym_whatsapp_instances")
        .select("gym_id, uazapi_instance_token")
        .eq("uazapi_instance_id", instance_id)
        .eq("active", True)
        .maybe_single()
        .execute()
    )
    if inst.data:
        gym = get_gym_by_id(inst.data["gym_id"])
        return gym, inst.data.get("uazapi_instance_token")

    legacy = (
        sb.table("gyms")
        .select("*")
        .eq("uazapi_instance_id", instance_id)
        .maybe_single()
        .execute()
    )
    if legacy.data:
        return legacy.data, legacy.data.get("uazapi_token")

    return None, None


def get_gym_by_instance(instance_id: str) -> dict[str, Any] | None:
    gym, _ = resolve_gym_from_uazapi_instance(instance_id)
    return gym


def count_active_whatsapp_instances(gym_id: str) -> int:
    sb = get_supabase()
    res = (
        sb.table("gym_whatsapp_instances")
        .select("id", count="exact")
        .eq("gym_id", gym_id)
        .eq("active", True)
        .execute()
    )
    return res.count or 0


def list_whatsapp_instances(gym_id: str) -> list[dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("gym_whatsapp_instances")
        .select("*")
        .eq("gym_id", gym_id)
        .order("created_at")
        .execute()
    )
    return res.data or []


def register_whatsapp_instance(
    gym_id: str,
    uazapi_instance_id: str,
    uazapi_instance_token: str,
    *,
    label: str = "WhatsApp",
    is_primary: bool = False,
) -> dict[str, Any]:
    sb = get_supabase()
    if count_active_whatsapp_instances(gym_id) >= 3:
        raise ValueError("Limite de 3 números WhatsApp por academia.")

    payload = {
        "gym_id": gym_id,
        "uazapi_instance_id": uazapi_instance_id,
        "uazapi_instance_token": uazapi_instance_token,
        "label": label,
        "is_primary": is_primary,
        "active": True,
    }
    res = sb.table("gym_whatsapp_instances").upsert(
        payload, on_conflict="uazapi_instance_id"
    ).execute()
    sb.table("gyms").update(
        {"uazapi_instance_id": uazapi_instance_id, "uazapi_token": uazapi_instance_token}
    ).eq("id", gym_id).execute()
    return res.data[0]


def get_or_create_member(
    gym_id: str,
    phone: str,
    wa_chatid: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    sb = get_supabase()
    existing = (
        sb.table("members")
        .select("*")
        .eq("gym_id", gym_id)
        .eq("phone", phone)
        .maybe_single()
        .execute()
    )
    if existing.data:
        updates: dict[str, Any] = {}
        if wa_chatid and existing.data.get("wa_chatid") != wa_chatid:
            updates["wa_chatid"] = wa_chatid
        if name and not existing.data.get("name"):
            updates["name"] = name
        if updates:
            sb.table("members").update(updates).eq("id", existing.data["id"]).execute()
            existing.data.update(updates)
        return existing.data

    payload = {
        "gym_id": gym_id,
        "phone": phone,
        "wa_chatid": wa_chatid,
        "name": name,
        "status": "lead",
    }
    created = sb.table("members").insert(payload).execute()
    return created.data[0]


def log_message(
    gym_id: str,
    wa_chatid: str,
    direction: str,
    body: str,
    member_id: str | None = None,
    raw: dict | None = None,
) -> None:
    sb = get_supabase()
    sb.table("messages").insert(
        {
            "gym_id": gym_id,
            "wa_chatid": wa_chatid,
            "member_id": member_id,
            "direction": direction,
            "body": body,
            "raw": raw,
        }
    ).execute()


def get_recent_messages(gym_id: str, wa_chatid: str, limit: int = 10) -> list[dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("messages")
        .select("direction, body, created_at")
        .eq("gym_id", gym_id)
        .eq("wa_chatid", wa_chatid)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(res.data or []))


def _normalize_text(value: str) -> str:
    import unicodedata

    n = unicodedata.normalize("NFD", value.lower())
    return "".join(c for c in n if unicodedata.category(c) != "Mn")


def _slot_local_date(starts_at: str) -> date:
    dt = datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ_BR).date()


def format_slot_br(starts_at: str) -> str:
    dt = datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ_BR).strftime("%d/%m/%Y %H:%M")


def list_available_slots(
    gym_id: str,
    modality: str | None = None,
    day: date | None = None,
    *,
    limit: int = 30,
) -> list[dict[str, Any]]:
    sb = get_supabase()
    query = (
        sb.table("class_slots")
        .select("id, modality, starts_at, ends_at, capacity, booked_count")
        .eq("gym_id", gym_id)
        .gte("starts_at", datetime.now(timezone.utc).isoformat())
        .order("starts_at")
        .limit(500)
    )
    res = query.execute()
    slots = res.data or []

    if modality:
        needle = _normalize_text(modality)
        slots = [s for s in slots if needle in _normalize_text(s["modality"])]

    if day:
        slots = [s for s in slots if _slot_local_date(s["starts_at"]) == day]

    available = [s for s in slots if s["booked_count"] < s["capacity"]]
    return available[:limit]


def list_plans(gym_id: str) -> list[dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("plans")
        .select("id, name, price_cents, description")
        .eq("gym_id", gym_id)
        .eq("active", True)
        .execute()
    )
    return res.data or []


def create_booking(gym_id: str, member_id: str, slot_id: str) -> dict[str, Any]:
    sb = get_supabase()
    slot_res = (
        sb.table("class_slots")
        .select("*")
        .eq("id", slot_id)
        .eq("gym_id", gym_id)
        .maybe_single()
        .execute()
    )
    slot = slot_res.data
    if not slot:
        return {"ok": False, "error": "Horário não encontrado."}
    if slot["booked_count"] >= slot["capacity"]:
        return {"ok": False, "error": "Este horário está lotado."}

    booking = (
        sb.table("bookings")
        .insert(
            {
                "gym_id": gym_id,
                "member_id": member_id,
                "slot_id": slot_id,
                "status": "confirmed",
            }
        )
        .execute()
    )

    sb.table("class_slots").update({"booked_count": slot["booked_count"] + 1}).eq(
        "id", slot_id
    ).execute()

    return {
        "ok": True,
        "booking_id": booking.data[0]["id"],
        "starts_at": slot["starts_at"],
        "modality": slot["modality"],
    }


def upsert_crm_contact(
    gym_id: str,
    wa_chatid: str,
    member_id: str | None,
    **fields: Any,
) -> None:
    sb = get_supabase()
    payload = {
        "gym_id": gym_id,
        "wa_chatid": wa_chatid,
        "member_id": member_id,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    sb.table("crm_contacts").upsert(payload, on_conflict="gym_id,wa_chatid").execute()
