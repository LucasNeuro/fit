"""
Teste rápido do agente no terminal (sem AgentOS).

  cd backend
  .venv\\Scripts\\activate
  python scripts/test_agent.py "Quais horários de funcional?"
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from core.ssl_fix import apply_dev_ssl_patches, configure_ssl  # noqa: E402

configure_ssl()
apply_dev_ssl_patches()

load_dotenv(BACKEND / ".env")
load_dotenv(BACKEND.parent / ".env")

from core.config import get_settings  # noqa: E402
from core import services  # noqa: E402
from core.logging_setup import setup_logging, startup_banner  # noqa: E402
from agents.runner import run_recepcionista  # noqa: E402

setup_logging()
startup_banner("test_agent.py")


def main() -> None:
    msg = " ".join(sys.argv[1:]) or "Olá, quais planos vocês têm?"
    settings = get_settings()

    print("--- FIT agent test ---")
    print(f"Mistral: {'OK' if settings.mistral_configured else 'FALTA MISTRAL_API_KEY'}")
    print(f"Supabase: {'OK' if settings.supabase_configured else 'FALTA (tools não funcionam)'}")
    print(f"Pergunta: {msg}\n")

    try:
        gym_id = services.resolve_session_gym_id()
    except services.GymContextRequired:
        gym_id = services.resolve_session_gym_id(slug="piloto")
    except RuntimeError as exc:
        print(f"Erro: {exc}")
        sys.exit(1)

    reply = run_recepcionista(
        gym_id=gym_id,
        member_id="os-demo-user",
        wa_chatid="5511999999999@s.whatsapp.net",
        user_message=msg,
    )
    print("Resposta:\n", reply)


if __name__ == "__main__":
    main()
