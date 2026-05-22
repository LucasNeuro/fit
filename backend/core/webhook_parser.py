"""Extrai e filtra payloads do webhook global UAZAPI."""

from __future__ import annotations

from typing import Any


def _dig(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def _is_truthy(val: Any) -> bool:
    if val is True or val == 1:
        return True
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes", "sim")
    return False


def should_process_webhook(body: dict[str, Any]) -> tuple[bool, str]:
    """
    Aplica filtros do painel UAZAPI:
    - eventos: messages (ignora connection-only sem texto)
    - exclui: wasSentByApi, isGroup
    """
    nested = body.get("data") or body.get("message") or body.get("event") or {}
    if not isinstance(nested, dict):
        nested = {}

    if _is_truthy(_dig(body, "wasSentByApi", "wasSentByAPI") or _dig(nested, "wasSentByApi")):
        return False, "wasSentByApi"

    if _is_truthy(_dig(body, "isGroup", "isGroupYes") or _dig(nested, "isGroup", "isGroupYes")):
        return False, "isGroup"

    event = str(_dig(body, "event", "type", "eventType") or _dig(nested, "event", "type") or "").lower()
    if event and event not in ("messages", "message", "chat", ""):
        if event == "connection":
            return False, "connection_event"

    return True, "ok"


def parse_inbound_message(body: dict[str, Any]) -> dict[str, Any]:
    """
    Retorna dict normalizado:
      text, wa_chatid, phone, instance_id, event
    """
    nested = body.get("data") or body.get("message") or body.get("event") or {}
    if not isinstance(nested, dict):
        nested = {}

    text = (
        _dig(body, "text", "body", "content", "messageText")
        or _dig(nested, "text", "body", "content", "messageText")
        or ""
    )
    if isinstance(text, dict):
        text = text.get("conversation") or text.get("text") or str(text)

    wa_chatid = (
        _dig(body, "wa_chatid", "chatId", "chatid", "remoteJid", "from")
        or _dig(nested, "wa_chatid", "chatId", "chatid", "remoteJid", "from")
    )

    phone = _dig(body, "phone", "number") or _dig(nested, "phone", "number")
    if wa_chatid and "@" in str(wa_chatid):
        phone = phone or str(wa_chatid).split("@")[0]

    instance_id = (
        _dig(body, "instanceId", "instance_id", "instance", "instanceName")
        or _dig(nested, "instanceId", "instance_id", "instance", "instanceName")
    )

    event = _dig(body, "event", "type") or _dig(nested, "event", "type")

    return {
        "text": str(text).strip(),
        "wa_chatid": str(wa_chatid) if wa_chatid else None,
        "phone": str(phone).replace("+", "").replace(" ", "") if phone else None,
        "instance_id": str(instance_id) if instance_id else None,
        "event": str(event) if event else None,
        "raw": body,
    }
