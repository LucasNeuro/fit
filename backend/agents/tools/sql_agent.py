"""
SQLTools Agno — interface agêntica de leitura no Postgres (Supabase).

Só permite SELECT. Escritas: criar_reserva, atualizar_lead_crm.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

from agno.tools.sql import SQLTools

from core.config import get_settings

logger = logging.getLogger("fit.sql")

# Tabelas do FIT (schema public)
FIT_TABLES = {
    "gyms": "Academias",
    "plans": "Planos e preços (price_cents)",
    "class_slots": "Horários de aula (modality, starts_at, capacity, booked_count)",
    "bookings": "Reservas de aula",
    "members": "Leads e alunos",
    "crm_contacts": "CRM / funil",
    "enrollments": "Matrículas",
    "messages": "Histórico de mensagens",
    "gym_whatsapp_instances": "Instâncias WhatsApp por academia",
}

_READONLY_PATTERN = re.compile(
    r"^\s*(with\b|select\b)",
    re.IGNORECASE | re.DOTALL,
)
_FORBIDDEN_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|copy)\b",
    re.IGNORECASE,
)


def _validate_readonly_sql(query: str) -> str | None:
    q = query.strip()
    if not q:
        return "Query vazia."
    if not _READONLY_PATTERN.match(q):
        return (
            "Só consultas SELECT (ou WITH ... SELECT) são permitidas. "
            "Para reservar ou CRM use criar_reserva / atualizar_lead_crm."
        )
    if _FORBIDDEN_PATTERN.search(q):
        return "Comando não permitido. Use apenas SELECT para leitura."
    return None


class FitReadonlySQLTools(SQLTools):
    """SQLTools com bloqueio de INSERT/UPDATE/DELETE."""

    def run_sql_query(self, query: str, limit: int | None = 25) -> str:
        err = _validate_readonly_sql(query)
        if err:
            logger.warning("SQL bloqueado: %s", err)
            return err
        return super().run_sql_query(query, limit=limit or 25)


@lru_cache
def get_fit_sql_tools() -> FitReadonlySQLTools | None:
    settings = get_settings()
    if not settings.database_configured:
        return None
    try:
        return FitReadonlySQLTools(
            db_url=settings.supabase_db_url,
            tables=FIT_TABLES,
            enable_list_tables=True,
            enable_describe_table=True,
            enable_run_sql_query=True,
        )
    except Exception as exc:
        logger.error("SQLTools indisponível: %s", exc)
        return None


def sql_tools_for_agent() -> list[Any]:
    toolkit = get_fit_sql_tools()
    return [toolkit] if toolkit else []
