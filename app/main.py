from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import time
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.routes import router as api_router
from app.core.settings import get_configs, get_settings
from app.struct_logger import logger, setup_logging


if TYPE_CHECKING:
    from collections.abc import Callable


WEB_DIR = Path(__file__).parent / "webapp"


def rate_limit_middleware(app: FastAPI) -> Callable:
    settings = get_settings()
    limit = settings.rate_limit_per_minute
    counters: dict[tuple[str, int], int] = {}
    last_cleanup: float = time.time()

    async def _middleware(request: Request, call_next):  # type: ignore[override]
        nonlocal last_cleanup
        if request.url.path.startswith("/api/calculate"):
            ip = request.client.host if request.client else "unknown"
            now_minute = int(time.time() // 60)
            key = (ip, now_minute)
            counters[key] = counters.get(key, 0) + 1
            if time.time() - last_cleanup > 300:
                stale_threshold = now_minute - 2
                for k in list(counters.keys()):
                    if k[1] < stale_threshold:
                        counters.pop(k, None)
                last_cleanup = time.time()
            if counters[key] > limit:
                logger.warning("rate_limited", ip=ip, limit=limit)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded", "limit_per_minute": limit},
                )
        return await call_next(request)

    return _middleware


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
app.middleware("http")(rate_limit_middleware(app))
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
