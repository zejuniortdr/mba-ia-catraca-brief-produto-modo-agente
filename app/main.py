from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/healthz")
    async def healthz():
        return {"ok": True}

    return app


app = create_app()
