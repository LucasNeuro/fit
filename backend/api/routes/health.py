from fastapi import APIRouter

from core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    s = get_settings()
    return {
        "status": "ok",
        "service": "fit-backend",
        "supabase": s.supabase_configured,
        "mistral": s.mistral_configured,
        "uazapi_server": s.uazapi_server_configured,
        "uazapi_can_send": s.uazapi_can_send(),
    }
