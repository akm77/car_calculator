from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import time
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.routes import router as api_router
from app.core.settings import get_configs, get_settings
from app.struct_logger import logger, setup_logging


if TYPE_CHECKING:
    from collections.abc import Callable


WEB_DIR = Path(__file__).parent / "webapp"


def _png_solid(width: int, height: int, rgba: tuple[int, int, int, int] = (36, 129, 204, 255)) -> bytes:
    """Generate a minimal solid-color PNG (RGBA) without external deps."""
    import struct, zlib, binascii

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    ihdr_chunk = chunk(b"IHDR", ihdr)

    r, g, b, a = rgba
    row = bytes([0]) + bytes([r, g, b, a]) * width  # filter byte 0 + pixels
    raw = row * height
    idat_chunk = chunk(b"IDAT", zlib.compress(raw, 9))
    iend_chunk = chunk(b"IEND", b"")
    return sig + ihdr_chunk + idat_chunk + iend_chunk


def rate_limit_middleware(app: FastAPI) -> Callable:
    settings = get_settings()
    limit = settings.rate_limit_per_minute
    counters: dict[tuple[str, int], int] = {}
    last_cleanup: float = time.time()

    async def _middleware(request: Request, call_next):
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
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("app_starting", web_dir=str(WEB_DIR))
    get_configs()  # Force load configs on startup
    yield
    # Shutdown
    logger.info("app_stopping")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    setup_logging()

    app = FastAPI(
        title="Car Import Calculator",
        description="Калькулятор растаможки автомобилей",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting middleware
    app.middleware("http")(rate_limit_middleware(app))

    # API routes
    app.include_router(api_router)

    # Dynamic icons for PWA so Lighthouse can fetch them even if files are missing
    @app.get("/assets/icon-192.png")
    async def icon_192() -> Response:
        return Response(content=_png_solid(192, 192), media_type="image/png")

    @app.get("/assets/icon-512.png")
    async def icon_512() -> Response:
        return Response(content=_png_solid(512, 512), media_type="image/png")

    # Static files for web interface - исправляем путь
    if WEB_DIR.exists():
        app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
        # html=True allows returning index.html for /web/ automatically
        app.mount("/web", StaticFiles(directory=WEB_DIR, html=True), name="webapp")
    else:
        logger.warning("webapp_dir_not_found", path=str(WEB_DIR))

    # Redirect root to /web/ to unify relative asset paths
    @app.get("/")
    async def root_redirect():
        return RedirectResponse(url="/web/")

    # manifest & sw kept at root for broader scope
    @app.get("/manifest.json")
    async def manifest():
        """Serve PWA manifest."""
        manifest_file = WEB_DIR / "manifest.json"
        if manifest_file.exists():
            return FileResponse(manifest_file, media_type="application/json")
        return JSONResponse(status_code=404, content={"detail": "Manifest not found"})

    # Дополнительный маршрут для service worker
    @app.get("/sw.js")
    async def service_worker():
        """Serve service worker."""
        sw_file = WEB_DIR / "sw.js"
        if sw_file.exists():
            return FileResponse(sw_file, media_type="application/javascript")
        return JSONResponse(status_code=404, content={"detail": "Service worker not found"})

    # Health check endpoint
    @app.get("/ping")
    async def ping():
        return {"status": "ok", "message": "pong"}

    # Debug endpoint для проверки файлов
    @app.get("/debug/files")
    async def debug_files():
        """Debug endpoint to check file structure."""
        files = {}
        if WEB_DIR.exists():
            for file in WEB_DIR.iterdir():
                files[file.name] = {
                    "exists": file.exists(),
                    "is_file": file.is_file(),
                    "size": file.stat().st_size if file.exists() else 0
                }
        return {
            "webapp_dir": str(WEB_DIR),
            "webapp_exists": WEB_DIR.exists(),
            "files": files
        }

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
