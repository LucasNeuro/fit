"""
Onboarding WhatsApp — criar instância via Admin API e conectar QR.

Usado quando a academia ainda não tem número no FIT (0 instâncias ativas).
No AgentOS simula o dono configurando o primeiro WhatsApp.
"""

from __future__ import annotations

from agno.run import RunContext
from agno.tools import tool

from core import services
from core.logging_setup import log_tool
from core.uazapi_admin import get_uazapi_admin


def _ctx(run_context: RunContext) -> dict:
    if not run_context.session_state:
        raise ValueError("session_state ausente")
    return run_context.session_state


@tool
def academia_tem_whatsapp(run_context: RunContext) -> str:
    """Verifica se a academia já tem instância WhatsApp cadastrada no FIT."""
    gym_id = _ctx(run_context)["gym_id"]
    log_tool("academia_tem_whatsapp", gym_id=gym_id)
    n = services.count_active_whatsapp_instances(gym_id)
    if n == 0:
        return "Nenhum WhatsApp conectado. Use iniciar_conexao_whatsapp para começar o onboarding."
    return f"A academia tem {n} instância(s) ativa(s). Pode usar horários e planos normalmente."


@tool
def iniciar_conexao_whatsapp(
    run_context: RunContext,
    nome_instancia: str = "",
    label: str = "Recepção",
) -> str:
    """
    Cria nova instância UAZAPI para esta academia e retorna instruções de QR/paircode.
    nome_instancia: ex 'academia-piloto-recepcao' (sem espaços)
    Máximo 3 instâncias por academia.
    """
    state = _ctx(run_context)
    gym_id = state["gym_id"]
    log_tool("iniciar_conexao_whatsapp", gym_id=gym_id, nome=nome_instancia, label=label)
    admin = get_uazapi_admin()

    if not admin.configured():
        return "Admin UAZAPI não configurado. Defina UAZAPI_ADMIN_TOKEN no servidor."

    existing = services.count_active_whatsapp_instances(gym_id)
    if existing >= 3:
        return "Esta academia já atingiu o limite de 3 números WhatsApp."

    gym = services.get_gym_by_id(gym_id)
    gym_name = (gym or {}).get("name", "academia")
    slug = (gym or {}).get("slug", "fit")
    name = nome_instancia.strip() or f"{slug}-wa-{existing + 1}"

    try:
        result = admin.create_instance(name=name, gym_id=gym_id, label=label)
    except Exception as e:
        return f"Erro ao criar instância na UAZAPI: {e}"

    inst = result.get("instance") or result
    instance_id = inst.get("id") or result.get("id")
    token = inst.get("token") or result.get("token")
    status = inst.get("status", "disconnected")
    paircode = inst.get("paircode") or ""
    qrcode = inst.get("qrcode") or ""

    if not instance_id or not token:
        return f"Resposta UAZAPI incompleta: {result}"

    services.register_whatsapp_instance(
        gym_id,
        instance_id,
        token,
        label=label,
        is_primary=existing == 0,
    )

    lines = [
        "Instância WhatsApp criada com sucesso.",
        f"ID: {instance_id}",
        f"Status: {status}",
    ]
    if paircode:
        lines.append(f"Código de pareamento: **{paircode}**")
    if qrcode and qrcode.startswith("data:image"):
        lines.append(
            "QR Code gerado. No painel UAZAPI ou no app WhatsApp → Aparelhos conectados → Conectar com número de telefone, escaneie o QR."
        )
        lines.append(
            "(No WhatsApp real, enviaremos a imagem do QR automaticamente quando esta instância estiver ativa.)"
        )
    else:
        lines.append("Abra o painel UAZAPI da instância para escanear o QR Code.")

    lines.append("Depois de conectar, diga **status whatsapp** para confirmar.")
    return "\n".join(lines)


@tool
def status_conexao_whatsapp(run_context: RunContext) -> str:
    """Consulta status das instâncias WhatsApp desta academia (connected / connecting / disconnected)."""
    gym_id = _ctx(run_context)["gym_id"]
    log_tool("status_conexao_whatsapp", gym_id=gym_id)
    admin = get_uazapi_admin()
    local = services.list_whatsapp_instances(gym_id)

    if not local:
        return "Nenhuma instância cadastrada. Use iniciar_conexao_whatsapp."

    lines = []
    for row in local:
        inst_id = row["uazapi_instance_id"]
        status = "desconhecido"
        if admin.configured():
            remote = admin.get_instance_by_id(inst_id)
            if remote:
                status = remote.get("status", "?")
                pname = remote.get("profileName") or ""
                if pname:
                    lines.append(f"- {row.get('label')}: **{status}** ({pname})")
                    continue
        lines.append(f"- {row.get('label')}: **{status}** (id {inst_id})")

    return "\n".join(lines)


ONBOARDING_TOOLS = [
    academia_tem_whatsapp,
    iniciar_conexao_whatsapp,
    status_conexao_whatsapp,
]
