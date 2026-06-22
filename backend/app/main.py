from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
import app.models  # noqa: F401 — registers all ORM models so FK resolution works on first flush
from app.api.routes import gaps, stats, reports, auth, audit

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FiscalAI API starting", environment=settings.environment)
    yield
    logger.info("FiscalAI API shutting down")


app = FastAPI(
    title="FiscalAI",
    description="Municipal Revenue Intelligence API — FiscalAI",
    version="0.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Routers — stats and reports must be registered before gaps so that
# /gaps/stats and /gaps/{id}/report resolve before /{gap_id} captures them.
app.include_router(auth.router,    prefix=settings.api_v1_prefix)
app.include_router(stats.router,   prefix=settings.api_v1_prefix)
app.include_router(reports.router, prefix=settings.api_v1_prefix)
app.include_router(audit.router,   prefix=settings.api_v1_prefix)
app.include_router(gaps.router,    prefix=settings.api_v1_prefix)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "fiscalai-api"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
    # ServerErrorMiddleware sits OUTSIDE CORSMiddleware, so its responses bypass
    # the CORS middleware and arrive at the browser without the required headers.
    # Add them manually so cross-origin callers see the error instead of an
    # opaque network failure.
    origin = request.headers.get("origin", "")
    cors_headers: dict[str, str] = {}
    if origin in settings.allowed_origins:
        cors_headers["Access-Control-Allow-Origin"] = origin
        cors_headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=cors_headers,
    )
