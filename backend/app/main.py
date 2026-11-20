from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.db import init_db
from app.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if settings.env == "production" and settings.secret in {
        "",
        "dev-only-change-me",
        "dev-only-change-me-not-for-production-use",
        "change-me-before-production",
    }:
        raise RuntimeError("Đặt JOBRADAR_SECRET trước khi chạy production")
    init_db()
    scheduler = start_scheduler()
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="JobRadar", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
