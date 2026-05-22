"""Factory do agente FIT (padrão Agno)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.mistral import MistralChat

from agents.tools.fit_tools import FIT_TOOLS
from core.config import get_settings
from core import services
from core.ssl_fix import mistral_client_params

PROMPT_PATH = Path(__file__).parent / "prompts" / "recepcionista.md"
AGENT_DB_PATH = Path(__file__).parent.parent / "tmp" / "fit_agent.db"

# Sessão fixa para testes no AgentOS (playground)
OS_DEMO_SESSION = "fit:os-demo"
OS_DEMO_USER = "os-demo-user"
OS_DEMO_CHAT = "5511999999999@s.whatsapp.net"


def _load_prompt_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_instructions(gym: dict[str, Any], gym_id: str, member_id: str, wa_chatid: str) -> list[str]:
    cfg = gym.get("agent_config") or {}
    if isinstance(cfg, str):
        import json

        cfg = json.loads(cfg)

    text = (
        _load_prompt_template()
        .replace("{{gym_name}}", gym.get("name", "Academia Piloto FIT"))
        .replace("{{assistant_name}}", cfg.get("assistant_name", "Ana"))
        .replace(
            "{{greeting}}",
            cfg.get("greeting", "Olá! Sou a Ana. Posso ajudar com horários, planos ou agendamento."),
        )
        .replace("{{gym_id}}", gym_id)
        .replace("{{member_id}}", member_id)
        .replace("{{wa_chatid}}", wa_chatid)
    )
    return [text]


def _get_agent_db() -> SqliteDb:
    AGENT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SqliteDb(db_file=str(AGENT_DB_PATH))


def create_recepcionista_agent(
    gym_id: str,
    member_id: str,
    wa_chatid: str,
    *,
    agent_id: str = "fit-recepcionista",
    session_id: str | None = None,
) -> Agent:
    """Cria instância Agno configurada para uma conversa."""
    settings = get_settings()
    gym = None
    if settings.supabase_configured:
        try:
            gym = services.get_gym_by_id(gym_id)
        except Exception:
            pass

    if not gym:
        gym = {
            "name": "Academia Piloto FIT",
            "agent_config": {
                "assistant_name": "Ana",
                "greeting": "Olá! Como posso ajudar?",
            },
        }

    sid = session_id or f"{gym_id}:{wa_chatid}"

    # WhatsApp conecta pelo painel admin (futuro) — agente só atende lead/aluno
    instructions = _build_instructions(gym, gym_id, member_id, wa_chatid)

    return Agent(
        id=agent_id,
        name="FIT Recepcionista",
        model=MistralChat(
            id=settings.agent_model_default,
            client_params=mistral_client_params() or None,
        ),
        db=_get_agent_db(),
        session_id=sid,
        user_id=member_id,
        session_state={
            "gym_id": gym_id,
            "member_id": member_id,
            "wa_chatid": wa_chatid,
        },
        instructions=instructions,
        tools=FIT_TOOLS,
        markdown=True,
        add_history_to_context=True,
        num_history_runs=5,
    )


def create_os_demo_agent() -> Agent:
    """
    Agente para testar no AgentOS (UI Agno).
    Usa DEFAULT_GYM_ID e sessão de demonstração.
    """
    settings = get_settings()
    gym_id = settings.default_gym_id
    member_id = OS_DEMO_USER
    wa_chatid = OS_DEMO_CHAT

    if settings.supabase_configured:
        try:
            member = services.get_or_create_member(
                gym_id,
                phone="5511999999999",
                wa_chatid=wa_chatid,
                name="Cliente Demo OS",
            )
            member_id = member["id"]
        except Exception:
            pass

    return create_recepcionista_agent(
        gym_id=gym_id,
        member_id=member_id,
        wa_chatid=wa_chatid,
        agent_id="fit-recepcionista",
        session_id=OS_DEMO_SESSION,
    )
