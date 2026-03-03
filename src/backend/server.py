from fastapi import Depends, FastAPI

from backend.api.routes.client import router as client_router
from backend.api.routes.messages import router as messages_router
from backend.core.dependencies.auth import verify_api_key
from backend.core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Chat Summarization Backend",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(
        messages_router,
        prefix="/v1/messages",
        tags=["Messages"],
        dependencies=[Depends(verify_api_key)],
    )
    app.include_router(
        client_router,
        prefix="/v1/client",
        tags=["Client"],
    )

    @app.get("/health", tags=["Health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
