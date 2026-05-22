"""Executa o agente FIT para mensagens WhatsApp (webhook)."""

from __future__ import annotations

import logging
import time

from agents.factory import create_recepcionista_agent
from core.config import get_settings
from core import services
from core.logging_setup import log_agent

logger = logging.getLogger(__name__)


def run_recepcionista(
    gym_id: str,
    member_id: str,
    wa_chatid: str,
    user_message: str,
) -> str:
    settings = get_settings()

    if not services.get_gym_by_id(gym_id) and settings.supabase_configured:
        log_agent(
            action="academia não encontrada",
            gym_id=gym_id,
            member_id=member_id,
            wa_chatid=wa_chatid,
            user_message=user_message,
        )
        return "Desculpe, não consegui identificar a academia. Tente novamente mais tarde."

    if not settings.mistral_configured:
        log_agent(
            action="Mistral não configurado",
            gym_id=gym_id,
            member_id=member_id,
            wa_chatid=wa_chatid,
            user_message=user_message,
        )
        return (
            f"Olá! Recebemos sua mensagem: «{user_message[:200]}». "
            "Configure MISTRAL_API_KEY no backend/.env para ativar o assistente."
        )

    agent = create_recepcionista_agent(gym_id, member_id, wa_chatid)
    log_agent(
        action="processando mensagem",
        gym_id=gym_id,
        member_id=member_id,
        wa_chatid=wa_chatid,
        user_message=user_message,
    )

    t0 = time.perf_counter()
    try:
        run_output = agent.run(user_message)
        content = getattr(run_output, "content", None) or str(run_output)
        reply = (
            content.strip()
            if content
            else "Posso ajudar com horários de aula ou planos da academia?"
        )
        elapsed = (time.perf_counter() - t0) * 1000
        log_agent(
            action="resposta pronta",
            gym_id=gym_id,
            member_id=member_id,
            wa_chatid=wa_chatid,
            reply=reply,
            elapsed_ms=elapsed,
        )
        return reply
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.exception("Erro no agente")
        log_agent(
            action="falha no agente",
            gym_id=gym_id,
            member_id=member_id,
            wa_chatid=wa_chatid,
            user_message=user_message,
            error=str(exc),
            elapsed_ms=elapsed,
        )
        return (
            "Desculpe, tive um problema técnico. "
            "Pode repetir sua pergunta ou digitar *atendente* para falar com a equipe?"
        )
