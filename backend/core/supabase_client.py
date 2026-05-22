from functools import lru_cache

import httpx
from supabase import Client, ClientOptions, create_client

from core.config import get_settings
from core.ssl_fix import configure_ssl, httpx_verify


def _httpx_client() -> httpx.Client:
    configure_ssl()
    return httpx.Client(verify=httpx_verify(), timeout=60.0)


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_configured:
        raise RuntimeError("Supabase não configurado. Defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY.")
    options = ClientOptions(httpx_client=_httpx_client())
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=options,
    )
