"""Operações de banco usadas pelo webhook e pelas tools."""

from __future__ import annotations

import uuid
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


class GymContextRequired(Exception):
    """Várias academias — agente deve chamar selecionar_academia."""


def list_gyms() -> list[dict[str, Any]]:
    sb = get_supabase()
    res = sb.table("gyms").select("id, name, slug, phone_whatsapp").order("name").execute()
    return res.data or []


def gym_is_operational(gym_id: str) -> bool:
    """Academia com planos ou horários futuros (ignora cadastro vazio/legado)."""
    try:
        summary = gym_data_summary(gym_id)
    except Exception:
        return False
    return summary["planos"] > 0 or summary["horarios_futuros"] > 0


def resolve_session_gym_id(
    *,
    gym_id: str | None = None,
    slug: str | None = None,
) -> str:
    """
    Resolve academia só pelo Supabase (sessão, slug ou única academia com dados).
    Ignora gym_id de sessão antiga se a academia não tiver planos/horários.
    """
    slug_clean = (slug or "").strip()
    if slug_clean:
        gym = get_gym_by_slug(slug_clean)
        if gym:
            return gym["id"]
        raise RuntimeError(f"Academia com slug '{slug_clean}' não encontrada.")

    gid = (gym_id or "").strip()
    if gid and get_gym_by_id(gid) and gym_is_operational(gid):
        return gid

    gyms = list_gyms()
    if not gyms:
        raise RuntimeError("Nenhuma academia no banco. Rode supabase/seed_piloto_completo.sql.")

    operational = [g for g in gyms if gym_is_operational(g["id"])]
    if len(operational) == 1:
        return operational[0]["id"]
    if len(operational) > 1:
        raise GymContextRequired(
            "Existem várias academias com dados. Use listar_academias e selecionar_academia(slug=...) "
            "antes de planos, horários ou reservas."
        )

    # Fallback: academia existe mas sem seed completo
    if gid and get_gym_by_id(gid):
        return gid
    if len(gyms) == 1:
        return gyms[0]["id"]

    raise GymContextRequired(
        "Nenhuma academia com planos/horários. Rode seed_piloto_completo.sql ou selecionar_academia."
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


def is_valid_member_id(member_id: str | None) -> bool:
    if not member_id:
        return False
    try:
        uuid.UUID(str(member_id))
        return True
    except ValueError:
        return False


def ensure_member_id(
    gym_id: str,
    *,
    member_id: str | None = None,
    wa_chatid: str | None = None,
    phone: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """
    Garante membro UUID válido no Supabase (AgentOS pode enviar e-mail no lugar de UUID).
    """
    if is_valid_member_id(member_id):
        existing = (
            get_supabase()
            .table("members")
            .select("*")
            .eq("id", member_id)
            .eq("gym_id", gym_id)
            .maybe_single()
            .execute()
        )
        if existing and existing.data:
            row = existing.data
            return row if isinstance(row, dict) else row[0]

    chat = wa_chatid or "5511999999999@s.whatsapp.net"
    tel = phone or chat.replace("@s.whatsapp.net", "").replace("@c.us", "")
    return get_or_create_member(gym_id, phone=tel, wa_chatid=chat, name=name or "Visitante")


def list_member_bookings(gym_id: str, member_id: str, limit: int = 10) -> list[dict[str, Any]]:
    sb = get_supabase()
    res = (
        sb.table("bookings")
        .select("id, status, created_at, slot_id, class_slots(modality, starts_at)")
        .eq("gym_id", gym_id)
        .eq("member_id", member_id)
        .neq("status", "cancelled")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


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
        .limit(1)
        .execute()
    )
    if existing.data:
        row = existing.data[0]
        updates: dict[str, Any] = {}
        if wa_chatid and row.get("wa_chatid") != wa_chatid:
            updates["wa_chatid"] = wa_chatid
        if name and not row.get("name"):
            updates["name"] = name
        if updates:
            sb.table("members").update(updates).eq("id", row["id"]).execute()
            row.update(updates)
        return row

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

    available = []
    for s in slots:
        active = count_confirmed_bookings(s["id"])
        if active != s.get("booked_count", 0):
            sync_slot_booked_count(s["id"])
            s["booked_count"] = active
        if active < s["capacity"]:
            s["booked_count"] = active
            available.append(s)
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


def count_confirmed_bookings(slot_id: str) -> int:
    """Fonte da verdade — reservas ativas no slot."""
    sb = get_supabase()
    res = (
        sb.table("bookings")
        .select("id", count="exact")
        .eq("slot_id", slot_id)
        .neq("status", "cancelled")
        .execute()
    )
    return res.count or 0


def sync_slot_booked_count(slot_id: str) -> int:
    """Alinha class_slots.booked_count com bookings (anti overbooking)."""
    count = count_confirmed_bookings(slot_id)
    sb = get_supabase()
    sb.table("class_slots").update({"booked_count": count}).eq("id", slot_id).execute()
    return count


def create_booking(gym_id: str, member_id: str, slot_id: str) -> dict[str, Any]:
    if not is_valid_member_id(member_id):
        return {
            "ok": False,
            "error": "member_id inválido — use ensure_member antes de reservar.",
        }

    sb = get_supabase()
    slot_res = (
        sb.table("class_slots")
        .select("*")
        .eq("id", slot_id)
        .eq("gym_id", gym_id)
        .maybe_single()
        .execute()
    )
    slot = slot_res.data if slot_res else None
    if not slot:
        return {"ok": False, "error": "Horário não encontrado."}

    active = count_confirmed_bookings(slot_id)
    if active >= slot["capacity"]:
        sync_slot_booked_count(slot_id)
        return {"ok": False, "error": "Este horário está lotado."}

    # Evita reserva duplicada do mesmo membro no mesmo slot
    dup = (
        sb.table("bookings")
        .select("id")
        .eq("slot_id", slot_id)
        .eq("member_id", member_id)
        .neq("status", "cancelled")
        .limit(1)
        .execute()
    )
    if dup.data:
        return {"ok": False, "error": "Você já tem reserva neste horário."}

    try:
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
    except Exception as exc:
        return {"ok": False, "error": f"Falha ao gravar no Supabase: {exc}"}

    if not booking.data:
        return {"ok": False, "error": "Reserva não foi gravada (resposta vazia do banco)."}

    new_count = sync_slot_booked_count(slot_id)

    return {
        "ok": True,
        "booking_id": booking.data[0]["id"],
        "starts_at": slot["starts_at"],
        "modality": slot["modality"],
        "booked_count": new_count,
        "capacity": slot["capacity"],
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
