from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

_ENV_FILES = (
    _BACKEND_DIR / ".env",
    _REPO_ROOT / ".env",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(p) for p in _ENV_FILES if p.exists()] or str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    log_level: str = "info"
    # false só em dev local se aparecer CERTIFICATE_VERIFY_FAILED (Windows/proxy)
    ssl_verify: bool = True

    # Mistral
    mistral_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # UAZAPI — servidor único (ex: onnzetecnologia.uazapi.com), várias instâncias/academias
    uazapi_base_url: str = "https://onnzetecnologia.uazapi.com"
    uazapi_admin_token: str = ""
    uazapi_send_text_path: str = "/send/text"

    # URL pública do backend (Render) — para configurar webhook global
    public_api_url: str = ""

    # Webhook global (query ?wh= igual ao configurado no painel UAZAPI)
    webhook_secret: str = ""
    webhook_validate_query: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # UUID da academia (seed). Se inválido, usa DEFAULT_GYM_SLUG.
    default_gym_id: str = ""
    default_gym_slug: str = "piloto"
    qr_signing_secret: str = "change-me-in-production"

    agent_model_default: str = "mistral-small-latest"
    agent_model_sales: str = "mistral-large-latest"
    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)

    @property
    def mistral_configured(self) -> bool:
        return bool(self.mistral_api_key)

    @property
    def uazapi_server_configured(self) -> bool:
        return bool(self.uazapi_base_url)

    @property
    def uazapi_admin_configured(self) -> bool:
        return bool(self.uazapi_base_url and self.uazapi_admin_token)

    def uazapi_can_send(self, token_from_db: str | None = None) -> bool:
        """Envio só com token da instância gravado no Supabase (sem fallback no .env)."""
        return bool(self.uazapi_base_url and (token_from_db or "").strip())

    def global_webhook_url(self) -> str:
        base = self.public_api_url.rstrip("/")
        if not base:
            return ""
        secret = self.webhook_secret
        if secret:
            return f"{base}/webhook/uazapi?wh={secret}"
        return f"{base}/webhook/uazapi"


@lru_cache
def get_settings() -> Settings:
    return Settings()
