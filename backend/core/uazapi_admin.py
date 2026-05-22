"""
Cliente Admin UAZAPI — criar/listar instâncias (servidor único).

Auth: header `admintoken` (não confundir com token da instância).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from core.config import get_settings
from core.logging_setup import log_uazapi
from core.ssl_fix import httpx_verify

logger = logging.getLogger(__name__)


class UazapiAdminClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.uazapi_base_url.rstrip("/")
        self.admin_token = settings.uazapi_admin_token

    def _headers(self) -> dict[str, str]:
        return {
            "admintoken": self.admin_token,
            "Content-Type": "application/json",
        }

    def configured(self) -> bool:
        return bool(self.base_url and self.admin_token)

    def create_instance(
        self,
        name: str,
        gym_id: str,
        label: str = "fit",
    ) -> dict[str, Any]:
        """POST /instance/create — adminField01 = gym_id no Supabase."""
        payload = {
            "name": name,
            "adminField01": gym_id,
            "adminField02": label,
        }
        with httpx.Client(timeout=60.0, verify=httpx_verify()) as client:
            r = client.post(
                f"{self.base_url}/instance/create",
                headers=self._headers(),
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            inst = data.get("instance") or data
            log_uazapi(
                action="instância criada",
                detail=f"id={inst.get('id')} status={inst.get('status')}",
                ok=True,
            )
            return data

    def list_instances(self) -> list[dict[str, Any]]:
        """GET /instance/all"""
        with httpx.Client(timeout=30.0, verify=httpx_verify()) as client:
            r = client.get(
                f"{self.base_url}/instance/all",
                headers=self._headers(),
            )
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else []

    def get_instance_by_id(self, instance_id: str) -> dict[str, Any] | None:
        for inst in self.list_instances():
            if inst.get("id") == instance_id:
                return inst
        return None

    def update_admin_fields(
        self,
        instance_id: str,
        admin_field01: str | None = None,
        admin_field02: str | None = None,
    ) -> dict[str, Any]:
        """POST /instance/updateAdminFields"""
        body: dict[str, str] = {"id": instance_id}
        if admin_field01 is not None:
            body["adminField01"] = admin_field01
        if admin_field02 is not None:
            body["adminField02"] = admin_field02
        with httpx.Client(timeout=30.0, verify=httpx_verify()) as client:
            r = client.post(
                f"{self.base_url}/instance/updateAdminFields",
                headers=self._headers(),
                json=body,
            )
            r.raise_for_status()
            return r.json()

    def configure_global_webhook(
        self,
        url: str,
        events: list[str] | None = None,
        exclude_messages: list[str] | None = None,
    ) -> dict[str, Any]:
        """POST /globalwebhook — configurar webhook global no servidor."""
        payload = {
            "url": url,
            "events": events or ["messages", "connection"],
            "excludeMessages": exclude_messages or ["wasSentByApi", "isGroupYes"],
            "addUrlEvents": False,
            "addUrlTypesMessages": False,
        }
        with httpx.Client(timeout=30.0, verify=httpx_verify()) as client:
            r = client.post(
                f"{self.base_url}/globalwebhook",
                headers=self._headers(),
                json=payload,
            )
            r.raise_for_status()
            return r.json()


def get_uazapi_admin() -> UazapiAdminClient:
    return UazapiAdminClient()
