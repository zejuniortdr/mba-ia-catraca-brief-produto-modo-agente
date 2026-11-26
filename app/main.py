import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app import auth, db, gateway
from app.cancellation import router as cancel_router
from app.checkin import router as checkin_router
from app.events import router as events_router
from app.partner_api import Unauthorized
from app.partner_api import router as partner_router
from app.routes import router
from app.seed import seed
from app.shop import router as shop_router
from app.web import render


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.open_pool()
    await db.apply_schema()
    async with db.pool.connection() as conn:
        await seed(conn)
    await gateway.reschedule_pending()
    yield
    await gateway.cancel_pending_tasks()
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

    @app.exception_handler(Unauthorized)
    async def unauthorized(request: Request, exc: Unauthorized):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    @app.get("/healthz")
    async def healthz():
        return {"ok": True}

    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(router)
    app.include_router(events_router)
    app.include_router(cancel_router)
    app.include_router(checkin_router)
    app.include_router(shop_router)
    app.include_router(partner_router)
    return app


app = create_app()
