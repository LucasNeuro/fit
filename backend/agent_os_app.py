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

from agents.factory import create_os_demo_agent

fit_agent = create_os_demo_agent()

agent_os = AgentOS(
    id="fit-agentos",
    name="FIT Superagente",
    description="Recepcionista digital para academias",
    agents=[fit_agent],
    tracing=False,
    telemetry=False,
)

app = agent_os.get_app()
