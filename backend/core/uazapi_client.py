import logging
from functools import lru_cache
from typing import Any

import httpx

from core.config import get_settings
from core.logging_setup import log_uazapi
from core.ssl_fix import httpx_verify

logger = logging.getLogger(__name__)


class UazapiClient:
    def __init__(self, instance_token: str | None = None) -> None:
        settings = get_settings()
        self.base_url = settings.uazapi_base_url.rstrip("/")
        self.token = (instance_token or "").strip()
        self.send_path = settings.uazapi_send_text_path

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            headers["token"] = self.token
        return headers

    def _can_call(self) -> bool:
        settings = get_settings()
        return settings.uazapi_can_send(self.token)

    async def send_text(self, chat_id: str, text: str) -> dict[str, Any]:
        if not self._can_call():
            log_uazapi(
                action="envio ignorado (sem token)",
                chat_id=chat_id,
                preview=text,
                ok=False,
                detail="uazapi_no_token",
            )
            return {"skipped": True, "reason": "uazapi_no_token"}

        payload = {
            "chatid": chat_id,
            "chatId": chat_id,
            "id": chat_id,
            "text": text,
            "message": text,
        }

        async with httpx.AsyncClient(timeout=30.0, verify=httpx_verify()) as client:
            response = await client.post(
                f"{self.base_url}{self.send_path}",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def edit_lead(self, chat_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.edit_lead_sync(chat_id, payload)

    def send_text_sync(self, chat_id: str, text: str) -> dict[str, Any]:
        if not self._can_call():
            logger.warning("UAZAPI sem token — mensagem não enviada: %s", text[:80])
            return {"skipped": True, "reason": "uazapi_no_token"}

        payload = {
            "chatid": chat_id,
            "chatId": chat_id,
            "id": chat_id,
            "text": text,
            "message": text,
        }
        with httpx.Client(timeout=30.0, verify=httpx_verify()) as client:
            response = client.post(
                f"{self.base_url}{self.send_path}",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def edit_lead_sync(self, chat_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._can_call():
            logger.warning("UAZAPI sem token — editLead ignorado")
            return {"skipped": True}

        body = {"id": chat_id, **payload}
        with httpx.Client(timeout=30.0, verify=httpx_verify()) as client:
            response = client.post(
                f"{self.base_url}/chat/editLead",
                headers=self._headers(),
                json=body,
            )
            response.raise_for_status()
            return response.json()


def get_uazapi(instance_token: str | None = None) -> UazapiClient:
    return UazapiClient(instance_token=instance_token)
