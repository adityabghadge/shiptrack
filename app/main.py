from fastapi import FastAPI

from app.api.incidents import router as incidents_router
from app.api.monitors import router as monitors_router
from app.api.results import router as results_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.models import Base
from app.db.session import engine


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title=settings.app_name)

   
    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)

    
    app.include_router(monitors_router, prefix="/api/v1")
    app.include_router(results_router, prefix="/api/v1")
    app.include_router(incidents_router, prefix="/api/v1")

    @app.get("/api/v1/health", tags=["ops"])
    def health():
        return {"status": "ok", "service": "api"}

    return app


app = create_app()