from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.routes import router as api_router
from app.core.settings import get_configs, get_settings
from app.struct_logger import logger, setup_logging


WEB_DIR = Path(__file__).parent / "webapp"


@asynccontextmanager
async def lifespan(app):
    settings = get_settings()
    setup_logging(settings.log_level)
    get_configs()  # preload configs
    logger.info("startup_complete", environment=settings.environment)
    try:
        yield
    finally:
        logger.info("shutdown")


app = FastAPI(title="Car Calculator API", lifespan=lifespan)
app.include_router(api_router)

if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/web")


def run_api() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_prod,
    )


if __name__ == "__main__":  # pragma: no cover
    run_api()
