"""
FIT AgentOS — app Agno (padrão documentação).

Subir com: python run.py
"""

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv

load_dotenv(_BACKEND / ".env")
load_dotenv(_BACKEND.parent / ".env")

from core.ssl_fix import apply_dev_ssl_patches, configure_ssl

configure_ssl()
apply_dev_ssl_patches()

from agno.os import AgentOS

import logging

from agents.factory import create_os_demo_agent
from core.config import get_settings
from core import services

logger = logging.getLogger("fit.agentos")

fit_agent = create_os_demo_agent()

settings = get_settings()
if settings.supabase_configured:
    try:
        gyms = services.list_gyms()
        print(f"  Supabase OK — {len(gyms)} academia(s) no banco")
        for g in gyms:
            stats = services.gym_data_summary(g["id"])
            print(
                f"    • {g['name']} (slug={g['slug']}) | "
                f"planos={stats['planos']} horarios={stats['horarios_futuros']}"
            )
        if len(gyms) > 1:
            print("  Várias academias: agente usa listar_academias / selecionar_academia")
        elif len(gyms) == 1:
            print(f"  gym_id ativo (única): {gyms[0]['id']}")
    except Exception as exc:
        logger.warning("Supabase: %s", exc)
        print(f"  AVISO Supabase: {exc}")
else:
    print("  AVISO: Supabase não configurado — tools não acessam o banco.")

agent_os = AgentOS(
    id="fit-agentos",
    name="FIT Superagente",
    description="Recepcionista digital para academias",
    agents=[fit_agent],
    tracing=False,
    telemetry=False,
)

app = agent_os.get_app()
