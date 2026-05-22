"""
Sobe o AgentOS FIT — teste no https://os.agno.com

  cd backend
  .venv\\Scripts\\activate
  python run.py

  IMPORTANTE: rode no TERMINAL e deixe aberto (nao use o botao Run do Cursor).

URL no painel Agno (Local): http://127.0.0.1:7780
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

AGENTOS_PORT = 7780

_BACKEND = Path(__file__).resolve().parent
os.chdir(_BACKEND)
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv

load_dotenv(_BACKEND / ".env")
load_dotenv(_BACKEND.parent / ".env")

from core.ssl_fix import apply_dev_ssl_patches, configure_ssl

configure_ssl()
apply_dev_ssl_patches()


def _free_port(port: int) -> None:
    if sys.platform != "win32":
        return
    ps = (
        f"Get-NetTCPConnection -LocalPort {port} -State Listen -EA SilentlyContinue | "
        "Select-Object -ExpandProperty OwningProcess -Unique | "
        "ForEach-Object { taskkill /F /PID $_ /T 2>$null }"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False)


def main() -> None:
    if ".venv" not in sys.executable.replace("\\", "/"):
        print("AVISO: ative o venv antes:  .venv\\Scripts\\activate")

    _free_port(AGENTOS_PORT)

    import uvicorn

    from agent_os_app import app

    url = f"http://127.0.0.1:{AGENTOS_PORT}"
    print()
    print("=" * 52)
    print("  FIT AgentOS ATIVO")
    print(f"  {url}")
    print("  os.agno.com -> Local -> URL acima -> REFRESH")
    print("  Deixe ESTE terminal aberto (Ctrl+C para parar)")
    print("=" * 52)
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=AGENTOS_PORT,
        reload=False,
        access_log=True,
    )


if __name__ == "__main__":
    main()
