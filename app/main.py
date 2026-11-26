import os
from contextlib import asynccontextmanager
from importlib.util import find_spec

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from app import auth, db
from app.events import router as events_router
from app.routes import router
from app.seed import seed
from app.web import render


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.open_pool()
    await db.apply_schema()
    async with db.pool.connection() as conn:
        await seed(conn)
    if find_spec("app.gateway"):  # F03 provides it
        from app import gateway

        await gateway.reschedule_pending()
    yield
    await db.pool.close()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.environ.get("SESSION_SECRET", "dev-secret-catraca"),
        same_site="lax",
    )

    @app.exception_handler(HTTPException)
    async def forbidden_page(request: Request, exc: HTTPException):
        if exc.status_code == 403:
            return render(request, "forbidden.html", await auth.current_user(request), 403)
        from fastapi.exception_handlers import http_exception_handler

        return await http_exception_handler(request, exc)

    @app.get("/healthz")
    async def healthz():
        return {"ok": True}

    app.include_router(router)
    app.include_router(events_router)
    return app


app = create_app()
