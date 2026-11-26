from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def render(request: Request, name: str, user: dict | None, status_code: int = 200, **ctx):
    return templates.TemplateResponse(request, name, {"user": user, **ctx}, status_code=status_code)
