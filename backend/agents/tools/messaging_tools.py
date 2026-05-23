"""
Tools UAZAPI — mensagens ricas no WhatsApp (botões, carrossel, PIX, etc.).

Requer session_state: wa_chatid, instance_token (preenchido no webhook).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from agno.run import RunContext
from agno.tools import tool

from core import services
from core.logging_setup import log_tool
from core.uazapi_client import get_uazapi

logger = logging.getLogger(__name__)


def _chat_and_token(run_context: RunContext) -> tuple[str | None, str | None, str | None]:
    state = run_context.session_state or {}
    wa_chatid = (state.get("wa_chatid") or "").strip()
    token = (state.get("instance_token") or "").strip()
    if not wa_chatid:
        return None, None, "wa_chatid ausente na sessão."
    if not token:
        return wa_chatid, None, "Token da instância ausente (só funciona no WhatsApp conectado)."
    return wa_chatid, token, None


def _mark_sent(run_context: RunContext) -> None:
    if run_context.session_state is not None:
        run_context.session_state["uazapi_messages_sent"] = True


def _parse_choices(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    if raw.startswith("["):
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise ValueError("opcoes JSON deve ser uma lista.")
        return [str(x) for x in parsed]
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _parse_carousel(raw: str) -> list[dict[str, Any]]:
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError("carrossel JSON deve ser uma lista de cartões.")
    return parsed


def _gym_id_from_ctx(run_context: RunContext) -> str | None:
    state = run_context.session_state or {}
    return (state.get("gym_id") or "").strip() or None


def _resolve_pix(
    run_context: RunContext,
    chave_pix: str = "",
    tipo_chave: str = "",
    nome_recebedor: str = "",
) -> tuple[str, str, str] | str:
    """Usa parâmetros explícitos ou PIX cadastrado na academia (gyms.pix_*)."""
    key = chave_pix.strip()
    ptype = tipo_chave.strip().upper()
    pname = nome_recebedor.strip()

    if not key:
        gym_id = _gym_id_from_ctx(run_context)
        if gym_id:
            cfg = services.get_gym_pix_config(gym_id)
            if cfg:
                key = cfg["pix_key"]
                ptype = ptype or cfg["pix_type"]
                pname = pname or cfg["pix_name"]

    if not key:
        return "ERRO: chave PIX não cadastrada para esta academia (gyms.pix_key)."
    if not ptype:
        ptype = "CNPJ"
    if not pname:
        pname = "Academia"
    return key, ptype, pname


@tool
def enviar_texto_whatsapp(
    run_context: RunContext,
    texto: str,
    delay_ms: int = 0,
    marcar_lido: bool = True,
) -> str:
    """
    Envia mensagem de texto simples no WhatsApp da conversa atual.
    Use delay_ms (ex. 800) para mostrar 'digitando...' antes de enviar.
    Prefira esta tool quando quiser controlar o envio; senão a resposta final também é enviada.
    """
    wa_chatid, token, err = _chat_and_token(run_context)
    if err:
        return f"ERRO: {err}"

    client = get_uazapi(token)
    result = client.send_text(
        wa_chatid,
        texto,
        delay=delay_ms or None,
        readchat=marcar_lido if marcar_lido else None,
    )
    if result.get("skipped"):
        return f"ERRO: envio ignorado ({result.get('reason')})."
    _mark_sent(run_context)
    log_tool("enviar_texto_whatsapp", ok=True, chat=wa_chatid)
    return "OK — texto enviado no WhatsApp."


@tool
def enviar_presenca_whatsapp(
    run_context: RunContext,
    tipo: str = "composing",
    duracao_ms: int = 15000,
) -> str:
    """
    Mostra 'digitando...' ou 'gravando áudio' enquanto processa.
    tipo: composing | recording | paused
    """
    wa_chatid, token, err = _chat_and_token(run_context)
    if err:
        return f"ERRO: {err}"

    client = get_uazapi(token)
    result = client.send_presence(wa_chatid, presence=tipo, delay=duracao_ms or None)
    if result.get("skipped"):
        return f"ERRO: {result.get('reason')}"
    return f"OK — presença '{tipo}' enviada."


@tool
def enviar_menu_whatsapp(
    run_context: RunContext,
    texto: str,
    tipo: str,
    opcoes: str,
    rodape: str = "",
    botao_lista: str = "Ver opções",
    imagem_botao: str = "",
) -> str:
    """
    Envia menu interativo UAZAPI.

    tipo: button | list | poll | carousel

    opcoes — JSON array ou uma opção por linha:
      Botões: "Ver planos|planos", "Horários|horarios", "Falar com humano|humano"
      Lista: "[Planos]", "Mensal|mensal|Acesso ilimitado", "[Aulas]", "Yoga|yoga|..."
      Enquete: "Manhã", "Tarde", "Noite"

    Após enviar menu, NÃO repita o mesmo conteúdo na resposta final.
    """
    wa_chatid, token, err = _chat_and_token(run_context)
    if err:
        return f"ERRO: {err}"

    try:
        choices = _parse_choices(opcoes)
    except (json.JSONDecodeError, ValueError) as exc:
        return f"ERRO ao interpretar opcoes: {exc}"

    if not choices:
        return "ERRO: informe ao menos uma opção."

    menu_type = tipo.strip().lower()
    if menu_type not in ("button", "list", "poll", "carousel"):
        return "ERRO: tipo deve ser button, list, poll ou carousel."

    client = get_uazapi(token)
    result = client.send_menu(
        wa_chatid,
        menu_type=menu_type,
        text=texto,
        choices=choices,
        footer_text=rodape or None,
        list_button=botao_lista if menu_type == "list" else None,
        selectable_count=1 if menu_type == "poll" else None,
        image_button=imagem_botao or None,
        readchat=True,
    )
    if result.get("skipped"):
        return f"ERRO: {result.get('reason')}"
    _mark_sent(run_context)
    log_tool("enviar_menu_whatsapp", ok=True, tipo=menu_type)
    return f"OK — menu '{menu_type}' enviado ({len(choices)} opções)."


@tool
def enviar_carrossel_whatsapp(
    run_context: RunContext,
    texto: str,
    cartoes_json: str,
) -> str:
    """
    Carrossel com imagens e botões (/send/carousel).

    cartoes_json — lista JSON com text, image, buttons (REPLY, URL, COPY, CALL).
    """
    wa_chatid, token, err = _chat_and_token(run_context)
    if err:
        return f"ERRO: {err}"

    try:
        carousel = _parse_carousel(cartoes_json)
    except (json.JSONDecodeError, ValueError) as exc:
        return f"ERRO ao interpretar cartoes_json: {exc}"

    client = get_uazapi(token)
    result = client.send_carousel(wa_chatid, text=texto, carousel=carousel, readchat=True)
    if result.get("skipped"):
        return f"ERRO: {result.get('reason')}"
    _mark_sent(run_context)
    log_tool("enviar_carrossel_whatsapp", ok=True, cards=len(carousel))
    return f"OK — carrossel enviado ({len(carousel)} cartões)."


@tool
def enviar_contato_whatsapp(
    run_context: RunContext,
    nome_completo: str,
    telefones: str,
    empresa: str = "",
    email: str = "",
    site: str = "",
) -> str:
    """
    Envia cartão de contato (vCard) — telefone da recepção ou personal.
    telefones: separados por vírgula, ex. "5511999887766,5511888776655"
    """
    wa_chatid, token, err = _chat_and_token(run_context)
    if err:
        return f"ERRO: {err}"

    client = get_uazapi(token)
    result = client.send_contact(
        wa_chatid,
        full_name=nome_completo,
        phone_number=telefones,
        organization=empresa or None,
        email=email or None,
        url=site or None,
        readchat=True,
    )
    if result.get("skipped"):
        return f"ERRO: {result.get('reason')}"
    _mark_sent(run_context)
    return "OK — cartão de contato enviado."


@tool
def enviar_botao_pix_whatsapp(
    run_context: RunContext,
    chave_pix: str = "",
    tipo_chave: str = "",
    nome_recebedor: str = "",
) -> str:
    """
    Envia botão PIX nativo do WhatsApp (matrícula / mensalidade).
    Se chave_pix vazio, usa gyms.pix_key cadastrada no Supabase.
    tipo_chave: CPF | CNPJ | PHONE | EMAIL | EVP
    """
    wa_chatid, token, err = _chat_and_token(run_context)
    if err:
        return f"ERRO: {err}"

    resolved = _resolve_pix(run_context, chave_pix, tipo_chave, nome_recebedor)
    if isinstance(resolved, str):
        return resolved
    key, ptype, pname = resolved

    client = get_uazapi(token)
    result = client.send_pix_button(
        wa_chatid,
        pix_key=key,
        pix_type=ptype,
        pix_name=pname,
        readchat=True,
    )
    if result.get("skipped"):
        return f"ERRO: {result.get('reason')}"
    _mark_sent(run_context)
    return "OK — botão PIX enviado."


@tool
def solicitar_pagamento_whatsapp(
    run_context: RunContext,
    valor_reais: float,
    descricao: str,
    titulo: str = "Pagamento",
    nome_item: str = "Matrícula / Plano",
    chave_pix: str = "",
    link_pagamento: str = "",
) -> str:
    """
    Solicita pagamento com botão 'Revisar e pagar' (PIX, boleto ou link).
    Use após cliente confirmar plano/matrícula. valor_reais ex.: 129.90
    """
    wa_chatid, token, err = _chat_and_token(run_context)
    if err:
        return f"ERRO: {err}"

    pix_key = chave_pix.strip()
    if not pix_key:
        resolved = _resolve_pix(run_context)
        if isinstance(resolved, str):
            return resolved
        pix_key, _, _ = resolved

    client = get_uazapi(token)
    result = client.send_request_payment(
        wa_chatid,
        amount=valor_reais,
        text=descricao,
        title=titulo,
        item_name=nome_item,
        pix_key=pix_key,
        payment_link=link_pagamento or None,
        readchat=True,
    )
    if result.get("skipped"):
        return f"ERRO: {result.get('reason')}"
    _mark_sent(run_context)
    return f"OK — solicitação de pagamento R$ {valor_reais:.2f} enviada."


MESSAGING_TOOLS = [
    enviar_texto_whatsapp,
    enviar_presenca_whatsapp,
    enviar_menu_whatsapp,
    enviar_carrossel_whatsapp,
    enviar_contato_whatsapp,
    enviar_botao_pix_whatsapp,
    solicitar_pagamento_whatsapp,
]
