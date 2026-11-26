from datetime import timedelta, timezone

from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def render(request: Request, name: str, user: dict | None, status_code: int = 200, **ctx):
    return templates.TemplateResponse(request, name, {"user": user, **ctx}, status_code=status_code)


def format_brl(cents: int) -> str:
    reais, c = divmod(cents, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{c:02d}"


# event and ticket statuses share one dict ("cancelled" reads the same in both)
STATUS_LABELS = {
    "draft": "rascunho",
    "published": "publicado",
    "cancelled": "cancelado",
    "pending": "pendente",
    "confirmed": "confirmado",
    "declined": "recusado",
    "refunded": "estornado",
}

templates.env.filters["brl"] = format_brl
templates.env.filters["status_label"] = lambda s: STATUS_LABELS[s]

templates.env.globals["tz"] = timezone(timedelta(hours=-3))
