"""
Tools FIT no padrão Agno: @tool + RunContext + session_state.

O agente recebe session_state com gym_id, member_id e wa_chatid.
Ver: https://docs.agno.com/tools/overview
"""

from __future__ import annotations

import logging

from datetime import date

from agno.run import RunContext
from agno.tools import tool

from core import services
from core.logging_setup import log_tool
from core.uazapi_client import get_uazapi


def _ctx(run_context: RunContext) -> dict:
    if not run_context.session_state:
        raise ValueError("session_state não configurado no Agent.")
    return run_context.session_state


def _is_uuid(value: str | None) -> bool:
    return services.is_valid_member_id(value)


def _resolve_write_context(
    run_context: RunContext,
    *,
    member_name: str | None = None,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Retorna (gym_id, member_id, wa_chatid, erro). Garante UUID no Supabase."""
    gym_id, err = _gym_id_from_ctx(run_context)
    if err:
        return None, None, None, err

    state = _ctx(run_context)
    wa_chatid = (state.get("wa_chatid") or "5511999999999@s.whatsapp.net").strip()

    try:
        member = services.ensure_member_id(
            gym_id,
            member_id=state.get("member_id"),
            wa_chatid=wa_chatid,
            name=member_name or state.get("member_name") or "Visitante chat",
        )
    except Exception as exc:
        return None, None, None, f"Não foi possível cadastrar o cliente: {exc}"

    state["member_id"] = member["id"]
    state["wa_chatid"] = wa_chatid
    return gym_id, member["id"], wa_chatid, None


def _gym_id_from_ctx(run_context: RunContext) -> tuple[str | None, str | None]:
    """
    Retorna (gym_id, mensagem_erro).
    Sempre reconcilia com Supabase — ignora gym_id vazio/legado sem horários.
    """
    state = _ctx(run_context)
    raw = (state.get("gym_id") or "").strip()
    try:
        gym_id = services.resolve_session_gym_id(gym_id=raw or None)
        if raw and raw != gym_id:
            logging.getLogger("fit.tool").info(
                "gym_id sessão %s -> %s (academia operacional no banco)", raw, gym_id
            )
        state["gym_id"] = gym_id
        return gym_id, None
    except services.GymContextRequired as exc:
        return None, str(exc)
    except RuntimeError as exc:
        return None, str(exc)


@tool
def listar_academias(run_context: RunContext) -> str:
    """Lista academias cadastradas no FIT (somente leitura). Use antes de selecionar_academia se houver mais de uma."""
    log_tool("listar_academias")
    try:
        gyms = services.list_gyms()
    except Exception as exc:
        return f"Não foi possível consultar academias: {exc}"
    if not gyms:
        return "Nenhuma academia no banco. Cadastre via painel ou seed SQL."
    lines = []
    for g in gyms:
        lines.append(f"- {g['name']} | slug={g['slug']} | gym_id={g['id']}")
    return "\n".join(lines)


@tool
def selecionar_academia(
    run_context: RunContext,
    slug: str = "",
    gym_id: str = "",
) -> str:
    """
    Define qual academia atender nesta conversa (consulta o banco).
    Informe slug (ex: piloto) ou gym_id (UUID).
    """
    log_tool("selecionar_academia", slug=slug, gym_id=gym_id)
    state = _ctx(run_context)
    try:
        resolved = services.resolve_session_gym_id(
            gym_id=gym_id.strip() or None,
            slug=slug.strip() or None,
        )
    except RuntimeError as exc:
        return str(exc)

    gym = services.get_gym_by_id(resolved)
    state["gym_id"] = resolved
    return f"Academia ativa: {gym.get('name') if gym else resolved} (gym_id={resolved}). Pode consultar planos e horários."


@tool
def listar_horarios(
    run_context: RunContext,
    modality: str = "",
    date_iso: str = "",
) -> str:
    """
    Lista horários disponíveis para agendamento.
    modality: ex funcional, musculação (opcional)
    date_iso: data AAAA-MM-DD no fuso de São Paulo (opcional; omita para ver próximos horários)
    """
    gym_id, err = _gym_id_from_ctx(run_context)
    if err:
        return err
    log_tool("listar_horarios", gym_id=gym_id, modality=modality, date=date_iso)
    day = date.fromisoformat(date_iso) if date_iso else None
    mod = modality.strip() or None
    slots = services.list_available_slots(gym_id, modality=mod, day=day)
    if not slots and day and not mod:
        slots = services.list_available_slots(gym_id)
    if not slots and mod:
        slots = services.list_available_slots(gym_id, day=day)
    if not slots:
        summary = services.gym_data_summary(gym_id)
        if summary["horarios_futuros"] == 0:
            return (
                "Não há horários futuros cadastrados para esta academia no banco. "
                "Rode supabase/seed_piloto_completo.sql no Supabase."
            )
        hint = ""
        if day or mod:
            hint = " (filtro de data/modalidade não encontrou nada — tente sem filtro)"
        return f"Não há vagas livres para esse filtro{hint}."
    lines = []
    for s in slots:
        vagas = s["capacity"] - s["booked_count"]
        quando = services.format_slot_br(s["starts_at"])
        lines.append(
            f"- slot_id={s['id']} | {s['modality']} | {quando} (BR) | {vagas} vaga(s)"
        )
    extra = ""
    total = services.gym_data_summary(gym_id)["horarios_futuros"]
    if len(slots) < total:
        extra = f"\n(mostrando {len(slots)} próximos horários com vaga)"
    return "\n".join(lines) + extra


@tool
def listar_planos(run_context: RunContext) -> str:
    """Lista planos ativos com preços oficiais da academia."""
    gym_id, err = _gym_id_from_ctx(run_context)
    if err:
        return err
    log_tool("listar_planos", gym_id=gym_id)
    plans = services.list_plans(gym_id)
    if not plans:
        return "Nenhum plano cadastrado no banco para esta academia. Rode seed_piloto_completo.sql."
    lines = []
    for p in plans:
        reais = p["price_cents"] / 100
        lines.append(f"- {p['name']}: R$ {reais:.2f} — {p.get('description') or ''}")
    return "\n".join(lines)


@tool
def criar_reserva(run_context: RunContext, slot_id: str) -> str:
    """
    GRAVA reserva no Supabase (tabelas bookings + class_slots).
    slot_id: UUID de listar_horarios ou run_sql_query.
    Só diga ao cliente que agendou se esta tool retornar booking_id=...
    """
    gym_id, member_id, wa_chatid, err = _resolve_write_context(run_context)
    if err:
        return err
    log_tool("criar_reserva", gym_id=gym_id, member_id=member_id, slot_id=slot_id)

    result = services.create_booking(gym_id, member_id, slot_id.strip())
    if not result.get("ok"):
        return f"ERRO — reserva NÃO gravada: {result.get('error')}"

    services.upsert_crm_contact(
        gym_id,
        wa_chatid,
        member_id,
        lead_status="experimental",
        lead_tags=["agendou"],
        field_03=result.get("modality"),
        field_05=str(result.get("starts_at")),
    )

    try:
        get_uazapi().edit_lead_sync(
            wa_chatid,
            {
                "lead_status": "experimental",
                "lead_tags": ["agendou"],
                "lead_field05": str(result.get("starts_at")),
            },
        )
    except Exception:
        pass

    quando = services.format_slot_br(str(result.get("starts_at")))
    return (
        f"OK — reserva GRAVADA no banco. "
        f"booking_id={result['booking_id']} | {result['modality']} | {quando} (BR) | "
        f"member_id={member_id}"
    )


@tool
def consultar_reservas_cliente(run_context: RunContext) -> str:
    """Lista reservas confirmadas do cliente atual no banco (verificação)."""
    gym_id, member_id, _, err = _resolve_write_context(run_context)
    if err:
        return err
    log_tool("consultar_reservas_cliente", gym_id=gym_id, member_id=member_id)
    rows = services.list_member_bookings(gym_id, member_id)
    if not rows:
        return "Nenhuma reserva confirmada no banco para este cliente."
    lines = []
    for r in rows:
        slot = r.get("class_slots") or {}
        quando = services.format_slot_br(slot.get("starts_at", "")) if slot.get("starts_at") else "?"
        lines.append(
            f"- booking_id={r['id']} | {slot.get('modality', '?')} | {quando} | status={r['status']}"
        )
    return "Reservas no sistema:\n" + "\n".join(lines)


@tool
def atualizar_lead_crm(
    run_context: RunContext,
    lead_status: str = "",
    tags: str = "",
    notes: str = "",
    open_ticket: bool = False,
) -> str:
    """
    Atualiza CRM do lead.
    lead_status: novo, contato, qualificado, experimental, matriculado, etc.
    tags: separadas por vírgula
    notes: anotações
    open_ticket: True para passar para humano
    """
    gym_id, member_id, wa_chatid, err = _resolve_write_context(run_context)
    if err:
        return err
    log_tool(
        "atualizar_lead_crm",
        gym_id=gym_id,
        status=lead_status,
        tags=tags,
        ticket=open_ticket,
    )

    fields: dict = {}
    if lead_status:
        fields["lead_status"] = lead_status
    if tags:
        fields["lead_tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    if notes:
        fields["lead_notes"] = notes
    if open_ticket:
        fields["lead_is_ticket_open"] = True
        if "lead_tags" not in fields:
            fields["lead_tags"] = []
        if "humano" not in fields["lead_tags"]:
            fields["lead_tags"].append("humano")

    services.upsert_crm_contact(gym_id, wa_chatid, member_id, **fields)

    uaz_payload: dict = {}
    if lead_status:
        uaz_payload["lead_status"] = lead_status
    if tags:
        uaz_payload["lead_tags"] = fields.get("lead_tags", [])
    if notes:
        uaz_payload["lead_notes"] = notes
    if open_ticket:
        uaz_payload["lead_isTicketOpen"] = True

    if uaz_payload:
        try:
            get_uazapi().edit_lead_sync(wa_chatid, uaz_payload)
        except Exception:
            pass

    return f"CRM gravado no banco para member_id={member_id}."


FIT_TOOLS = [
    listar_academias,
    selecionar_academia,
    listar_horarios,
    listar_planos,
    criar_reserva,
    consultar_reservas_cliente,
    atualizar_lead_crm,
]
