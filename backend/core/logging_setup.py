"""
Logging FIT com Rich — saída clara no terminal.

Uso no início de cada entrypoint:
    from core.logging_setup import setup_logging
    setup_logging()
"""

from __future__ import annotations

import logging
import sys
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.config import get_settings

F = TypeVar("F", bound=Callable[..., Any])

_configured = False
_console: Console | None = None

# Cores por categoria de evento
_STYLES = {
    "webhook": "bold cyan",
    "agent": "bold magenta",
    "tool": "bold yellow",
    "uazapi": "bold green",
    "supabase": "bold blue",
    "startup": "bold white on dark_blue",
    "skip": "dim",
    "error": "bold red",
    "ok": "bold green",
}


def get_console() -> Console:
    global _console
    if _console is None:
        _console = Console(stderr=True, highlight=False)
    return _console


def _level_from_settings() -> int:
    raw = get_settings().log_level.strip().upper()
    return getattr(logging, raw, logging.INFO)


def setup_logging(*, force: bool = False) -> None:
    """Configura root logger com RichHandler (idempotente)."""
    global _configured
    if _configured and not force:
        return

    level = _level_from_settings()
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = RichHandler(
        console=get_console(),
        rich_tracebacks=True,
        tracebacks_show_locals=get_settings().env == "development",
        markup=True,
        show_time=True,
        show_path=True,
        omit_repeated_times=False,
    )
    handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    root.addHandler(handler)

    # Menos ruído de libs HTTP
    for name in ("httpx", "httpcore", "hpack", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)

    _configured = True


def startup_banner(service: str, **extra: str) -> None:
    """Painel de boot ao subir API ou AgentOS."""
    setup_logging()
    table = Table.grid(padding=(0, 1))
    table.add_column(style="dim")
    table.add_column()
    table.add_row("serviço", f"[bold]{service}[/]")
    settings = get_settings()
    table.add_row("ambiente", settings.env)
    table.add_row("log", settings.log_level)
    table.add_row("mistral", "OK" if settings.mistral_configured else "FALTA MISTRAL_API_KEY")
    table.add_row("supabase", "OK" if settings.supabase_configured else "FALTA")
    table.add_row("uazapi admin", "OK" if settings.uazapi_admin_configured else "FALTA")
    for k, v in extra.items():
        table.add_row(k, v)

    get_console().print(
        Panel(table, title="FIT", border_style="blue", padding=(1, 2))
    )


def _truncate(text: str, max_len: int = 120) -> str:
    t = (text or "").replace("\n", " ").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def event_panel(
    category: str,
    title: str,
    rows: dict[str, Any] | None = None,
    *,
    style: str | None = None,
) -> None:
    """Painel estruturado para eventos importantes."""
    setup_logging()
    cat_style = style or _STYLES.get(category, "white")
    table = Table.grid(padding=(0, 1))
    table.add_column(style="dim", justify="right")
    table.add_column()
    if rows:
        for key, val in rows.items():
            if val is None or val == "":
                continue
            table.add_row(str(key), str(val))

    header = Text()
    header.append(f"[{category}] ", style=cat_style)
    header.append(title)

    get_console().print(
        Panel(
            table if rows else Text("—", style="dim"),
            title=header,
            border_style=cat_style.split()[-1] if " " in cat_style else "cyan",
            padding=(0, 1),
        )
    )


def log_webhook(
    *,
    action: str,
    instance_id: str | None = None,
    gym_id: str | None = None,
    phone: str | None = None,
    text: str | None = None,
    reason: str | None = None,
    queued: bool | None = None,
) -> None:
    rows: dict[str, Any] = {}
    if instance_id:
        rows["instance"] = _truncate(instance_id, 24)
    if gym_id:
        rows["gym_id"] = _truncate(gym_id, 36)
    if phone:
        rows["telefone"] = phone
    if text:
        rows["mensagem"] = _truncate(text, 200)
    if reason:
        rows["motivo"] = reason
    if queued is not None:
        rows["fila"] = "sim" if queued else "não"

    style = _STYLES["skip"] if action in ("ignorado", "skip") else _STYLES["webhook"]
    event_panel("webhook", action, rows, style=style)
    logging.getLogger("fit.webhook").info("%s | %s", action, rows or {})


def log_agent(
    *,
    action: str,
    gym_id: str,
    member_id: str,
    wa_chatid: str,
    user_message: str | None = None,
    reply: str | None = None,
    elapsed_ms: float | None = None,
    error: str | None = None,
) -> None:
    rows: dict[str, Any] = {
        "gym": _truncate(gym_id, 36),
        "membro": _truncate(member_id, 36),
        "chat": _truncate(wa_chatid, 40),
    }
    if user_message:
        rows["entrada"] = _truncate(user_message, 200)
    if reply:
        rows["resposta"] = _truncate(reply, 200)
    if elapsed_ms is not None:
        rows["tempo"] = f"{elapsed_ms:.0f} ms"
    if error:
        rows["erro"] = _truncate(error, 300)

    style = _STYLES["error"] if error else _STYLES["agent"]
    event_panel("agent", action, rows, style=style)
    logging.getLogger("fit.agent").info("%s gym=%s", action, gym_id[:8])


def log_tool(name: str, **params: Any) -> None:
    rows = {k: _truncate(str(v), 80) for k, v in params.items() if v is not None}
    event_panel("tool", name, rows or None, style=_STYLES["tool"])
    logging.getLogger("fit.tool").debug("tool %s %s", name, rows)


def log_uazapi(
    *,
    action: str,
    chat_id: str | None = None,
    preview: str | None = None,
    ok: bool = True,
    detail: str | None = None,
) -> None:
    rows: dict[str, Any] = {}
    if chat_id:
        rows["chat"] = _truncate(chat_id, 40)
    if preview:
        rows["texto"] = _truncate(preview, 120)
    if detail:
        rows["detalhe"] = detail

    style = _STYLES["ok"] if ok else _STYLES["error"]
    event_panel("uazapi", action, rows or None, style=style)
    logging.getLogger("fit.uazapi").info("%s %s", action, rows or {})


def timed_agent(fn: F) -> F:
    """Decorator opcional para medir tempo de execução."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - t0) * 1000
            logging.getLogger("fit.agent").debug("%.0f ms", elapsed)

    return wrapper  # type: ignore[return-value]
