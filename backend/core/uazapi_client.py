import logging
from typing import Any

import httpx

from core.config import get_settings
from core.logging_setup import log_uazapi
from core.ssl_fix import httpx_verify

logger = logging.getLogger(__name__)

# Campos opcionais comuns (UAZAPI "Enviar Mensagem")
COMMON_SEND_FIELDS = frozenset(
    {
        "delay",
        "readchat",
        "readmessages",
        "replyid",
        "mentions",
        "forward",
        "track_source",
        "track_id",
        "async",
    }
)


class UazapiClient:
    def __init__(self, instance_token: str | None = None) -> None:
        settings = get_settings()
        self.base_url = settings.uazapi_base_url.rstrip("/")
        self.token = (instance_token or "").strip()
        self.send_path = settings.uazapi_send_text_path

    @staticmethod
    def _normalize_number(chat_id: str) -> str:
        """UAZAPI exige `number` (só dígitos), não chatid completo."""
        raw = chat_id.strip()
        if "@" in raw:
            raw = raw.split("@", 1)[0]
        return raw.replace("+", "").replace(" ", "")

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["token"] = self.token
        return headers

    def _can_call(self) -> bool:
        settings = get_settings()
        return settings.uazapi_can_send(self.token)

    def _with_number(self, chat_id: str, **fields: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {"number": self._normalize_number(chat_id)}
        for key, value in fields.items():
            if value is not None:
                payload[key] = value
        return payload

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._can_call():
            log_uazapi(
                action="envio ignorado (sem token)",
                ok=False,
                detail="uazapi_no_token",
            )
            return {"skipped": True, "reason": "uazapi_no_token"}

        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=60.0, verify=httpx_verify()) as client:
            response = client.post(url, headers=self._headers(), json=payload)
            if response.status_code >= 400:
                logger.error("UAZAPI %s %s: %s", response.status_code, path, response.text[:500])
            response.raise_for_status()
            try:
                return response.json()
            except Exception:
                return {"ok": True, "raw": response.text}

    async def _apost(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._can_call():
            return {"skipped": True, "reason": "uazapi_no_token"}

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=60.0, verify=httpx_verify()) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
            if response.status_code >= 400:
                logger.error("UAZAPI %s %s: %s", response.status_code, path, response.text[:500])
            response.raise_for_status()
            try:
                return response.json()
            except Exception:
                return {"ok": True, "raw": response.text}

    # --- Texto ---

    def send_text(
        self,
        chat_id: str,
        text: str,
        *,
        delay: int | None = None,
        readchat: bool | None = None,
        replyid: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        payload = self._with_number(chat_id, text=text, delay=delay, readchat=readchat, replyid=replyid, **extra)
        return self._post(self.send_path, payload)

    async def send_text_async(self, chat_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        payload = self._with_number(chat_id, text=text, **kwargs)
        return await self._apost(self.send_path, payload)

    def send_text_sync(self, chat_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        return self.send_text(chat_id, text, **kwargs)

    # --- Presença (digitando / gravando) ---

    def send_presence(
        self,
        chat_id: str,
        presence: str = "composing",
        *,
        delay: int | None = None,
    ) -> dict[str, Any]:
        """presence: composing | recording | paused"""
        payload = self._with_number(chat_id, presence=presence, delay=delay)
        return self._post("/message/presence", payload)

    async def send_presence_async(
        self,
        chat_id: str,
        presence: str = "composing",
        *,
        delay: int | None = None,
    ) -> dict[str, Any]:
        payload = self._with_number(chat_id, presence=presence, delay=delay)
        return await self._apost("/message/presence", payload)

    # --- Menu interativo (botões, lista, enquete, carousel legado) ---

    def send_menu(
        self,
        chat_id: str,
        *,
        menu_type: str,
        text: str,
        choices: list[str],
        footer_text: str | None = None,
        list_button: str | None = None,
        selectable_count: int | None = None,
        image_button: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        payload = self._with_number(
            chat_id,
            type=menu_type,
            text=text,
            choices=choices,
            footerText=footer_text,
            listButton=list_button,
            selectableCount=selectable_count,
            imageButton=image_button,
            **extra,
        )
        return self._post("/send/menu", payload)

    # --- Carrossel estruturado ---

    def send_carousel(
        self,
        chat_id: str,
        *,
        text: str,
        carousel: list[dict[str, Any]],
        **extra: Any,
    ) -> dict[str, Any]:
        payload = self._with_number(chat_id, text=text, carousel=carousel, **extra)
        return self._post("/send/carousel", payload)

    # --- Contato vCard ---

    def send_contact(
        self,
        chat_id: str,
        *,
        full_name: str,
        phone_number: str,
        organization: str | None = None,
        email: str | None = None,
        url: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        payload = self._with_number(
            chat_id,
            fullName=full_name,
            phoneNumber=phone_number,
            organization=organization,
            email=email,
            url=url,
            **extra,
        )
        return self._post("/send/contact", payload)

    # --- Localização ---

    def send_location_button(self, chat_id: str, text: str, **extra: Any) -> dict[str, Any]:
        payload = self._with_number(chat_id, text=text, **extra)
        return self._post("/send/location-button", payload)

    # --- PIX (matrícula / cobrança futura) ---

    def send_pix_button(
        self,
        chat_id: str,
        *,
        pix_key: str,
        pix_type: str = "EVP",
        pix_name: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        payload = self._with_number(
            chat_id,
            pixKey=pix_key,
            pixType=pix_type.upper(),
            pixName=pix_name or "Pix",
            **extra,
        )
        return self._post("/send/pix-button", payload)

    def send_request_payment(
        self,
        chat_id: str,
        *,
        amount: float,
        text: str,
        title: str | None = None,
        item_name: str | None = None,
        pix_key: str | None = None,
        pix_type: str | None = None,
        payment_link: str | None = None,
        file_url: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        payload = self._with_number(
            chat_id,
            amount=amount,
            text=text,
            title=title,
            itemName=item_name,
            pixKey=pix_key,
            pixType=pix_type,
            paymentLink=payment_link,
            fileUrl=file_url,
            **extra,
        )
        return self._post("/send/request-payment", payload)

    # --- CRM ---

    async def edit_lead(self, chat_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.edit_lead_sync(chat_id, payload)

    def edit_lead_sync(self, chat_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._can_call():
            logger.warning("UAZAPI sem token — editLead ignorado")
            return {"skipped": True}

        body = {"id": chat_id, **payload}
        return self._post("/chat/editLead", body)


def get_uazapi(instance_token: str | None = None) -> UazapiClient:
    return UazapiClient(instance_token=instance_token)
