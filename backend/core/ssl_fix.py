"""
Corrige SSL no Windows: CERTIFICATE_VERIFY_FAILED ao chamar Supabase/Mistral.

Deve rodar antes de qualquer cliente HTTP (importar no topo dos entrypoints).
"""

from __future__ import annotations

import logging
import os
import ssl

logger = logging.getLogger(__name__)

_configured = False


def configure_ssl() -> None:
    """Usa bundle certifi para validação HTTPS (comum no Windows)."""
    global _configured
    if _configured:
        return

    try:
        import certifi
    except ImportError:
        logger.warning("certifi não instalado — pip install certifi")
        return

    cafile = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", cafile)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", cafile)

    _configured = True


def apply_dev_ssl_patches() -> None:
    """Desativa verificação SSL em todos os httpx (Mistral/Agno) quando SSL_VERIFY=false."""
    from core.config import get_settings

    if get_settings().ssl_verify:
        return

    import httpx

    logger.warning("SSL_VERIFY=false — httpx sem verificação SSL (só dev local)")

    # Fallback para libs que não usam httpx (urllib, requests antigos)
    try:
        ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        from agno.utils.http import set_default_async_client, set_default_sync_client

        set_default_sync_client(httpx.Client(verify=False, timeout=60.0))
        set_default_async_client(httpx.AsyncClient(verify=False, timeout=60.0))
    except Exception as exc:
        logger.debug("Agno http defaults: %s", exc)

    try:
        from core.supabase_client import get_supabase

        get_supabase.cache_clear()
    except Exception:
        pass


def mistral_client_params() -> dict:
    """Parâmetros para MistralChat(client_params=...) quando SSL_VERIFY=false."""
    from core.config import get_settings

    if get_settings().ssl_verify:
        return {}

    import httpx

    return {
        "client": httpx.Client(verify=False, timeout=120.0),
        "async_client": httpx.AsyncClient(verify=False, timeout=120.0),
    }


def httpx_verify():
    """Parâmetro verify= para httpx.Client / AsyncClient."""
    configure_ssl()

    # Import tardio para evitar ciclo com config
    from core.config import get_settings

    if not get_settings().ssl_verify:
        logger.warning("SSL_VERIFY=false — use só em desenvolvimento local")
        return False

    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return True
