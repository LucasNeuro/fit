import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request

from agents.runner import run_recepcionista
from core.config import get_settings
from core.logging_setup import log_uazapi, log_webhook
from core.services import (
    get_gym_by_id,
    get_or_create_member,
    log_message,
    resolve_gym_from_uazapi_instance,
)
from core.uazapi_client import get_uazapi
from core.webhook_parser import parse_inbound_message, should_process_webhook

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhook"])


def _validate_webhook_secret(wh: str | None) -> None:
    settings = get_settings()
    if not settings.webhook_validate_query or not settings.webhook_secret:
        return
    if wh != settings.webhook_secret:
        log_webhook(action="webhook rejeitado", reason="secret inválido")
        raise HTTPException(status_code=401, detail="webhook secret invalid")


def _resolve_gym(instance_id: str | None) -> tuple[dict | None, str | None]:
    if not instance_id:
        logger.warning("Webhook sem instance_id — ignore (não usar academia chumbada)")
        return None, None

    gym, token = resolve_gym_from_uazapi_instance(instance_id)
    if gym:
        return gym, token

    # Tentativa: adminField01 = gym_id na instância UAZAPI
    from core.uazapi_admin import get_uazapi_admin

    admin = get_uazapi_admin()
    if admin.configured():
        remote = admin.get_instance_by_id(instance_id)
        if remote and remote.get("adminField01"):
            gym = get_gym_by_id(str(remote["adminField01"]))
            if gym:
                token = remote.get("token")
                return gym, token

    logger.warning("Instância UAZAPI não mapeada: %s", instance_id)
    return None, None


async def _process_message(
    gym_id: str,
    wa_chatid: str,
    phone: str,
    text: str,
    member_id: str,
    raw: dict,
    instance_token: str | None,
) -> None:
    if not text:
        return

    log_message(gym_id, wa_chatid, "in", text, member_id=member_id, raw=raw)

    reply = run_recepcionista(gym_id, member_id, wa_chatid, text)

    log_message(gym_id, wa_chatid, "out", reply, member_id=member_id)

    uazapi = get_uazapi(instance_token)
    try:
        await uazapi.send_text(wa_chatid, reply)
        log_uazapi(action="mensagem enviada", chat_id=wa_chatid, preview=reply, ok=True)
    except Exception as exc:
        logger.error("Falha ao enviar WhatsApp: %s", exc)
        log_uazapi(
            action="falha ao enviar",
            chat_id=wa_chatid,
            preview=reply,
            ok=False,
            detail=str(exc),
        )


async def uazapi_webhook_handler(
    request: Request,
    background_tasks: BackgroundTasks,
    wh: str | None = Query(None, description="Segredo do webhook global (?wh=)"),
) -> dict:
    """
    Webhook global UAZAPI — uma URL para todas as academias/instâncias.

    URLs aceitas:
      POST /webhook/uazapi?wh=SEU_SECRET
      POST /api/whatsapp/webhook?wh=SEU_SECRET  (compatível com painel)
    """
    _validate_webhook_secret(wh)

    try:
        body = await request.json()
    except Exception:
        body = {}

    if not isinstance(body, dict):
        body = {"data": body}

    ok, reason = should_process_webhook(body)
    if not ok:
        log_webhook(action="ignorado", reason=reason)
        return {"ok": True, "skipped": reason}

    parsed = parse_inbound_message(body)
    text = parsed.get("text") or ""
    wa_chatid = parsed.get("wa_chatid")
    phone = parsed.get("phone")
    instance_id = parsed.get("instance_id")

    if not wa_chatid and not phone:
        log_webhook(action="ignorado", reason="sem chat_id")
        return {"ok": True, "skipped": "no_chat_id"}

    gym, instance_token = _resolve_gym(instance_id)
    if not gym:
        log_webhook(
            action="academia não encontrada",
            instance_id=instance_id,
            reason="gym_not_found",
        )
        return {"ok": False, "error": "gym_not_found", "instance_id": instance_id}

    gym_id = gym["id"]
    if not phone:
        phone = str(wa_chatid).split("@")[0]

    member = get_or_create_member(gym_id, phone, wa_chatid=wa_chatid)
    member_id = member["id"]
    chat_id = wa_chatid or f"{phone}@s.whatsapp.net"

    log_webhook(
        action="mensagem recebida",
        instance_id=instance_id,
        gym_id=gym_id,
        phone=phone,
        text=text or "(sem texto)",
        queued=bool(text),
    )

    if text:
        background_tasks.add_task(
            _process_message,
            gym_id,
            chat_id,
            phone,
            text,
            member_id,
            body,
            instance_token,
        )

    return {
        "ok": True,
        "queued": bool(text),
        "gym_id": gym_id,
        "instance_id": instance_id,
    }


@router.post("/webhook/uazapi")
async def uazapi_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    wh: str | None = Query(None),
):
    return await uazapi_webhook_handler(request, background_tasks, wh)


@router.post("/api/whatsapp/webhook")
async def uazapi_webhook_legacy_path(
    request: Request,
    background_tasks: BackgroundTasks,
    wh: str | None = Query(None),
):
    """Mesmo handler — path usado no painel Webhook Global."""
    return await uazapi_webhook_handler(request, background_tasks, wh)
