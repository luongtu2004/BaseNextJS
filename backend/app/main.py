from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from app.api.v1.docs import get_swagger_html, customize_swagger_docs
from app.api.v1.router import api_router
from app.api.v1.swagger_login import swagger_login_router
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.db.session import AsyncSessionLocal, engine, import_models
from app.middleware.request_logging import RequestLoggingMiddleware

settings = get_settings()

# ── Initialize logging BEFORE anything else ──────────────────────────
setup_logging(
    log_level=settings.log_level,
    log_dir=settings.log_dir,
    log_sql=settings.log_sql,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import logging
    logger = logging.getLogger("app.main")
    logger.info("Application starting up...")
    import_models()
    logger.info("All ORM models loaded successfully")
    yield
    logger.info("Application shutting down...")
    await engine.dispose()
    logger.info("Database engine disposed")


app = FastAPI(
    title="Sàn Dịch Vụ API - With Phone Authentication",
    version="0.1.0",
    docs_url=None,  # Disable default Swagger UI
    redoc_url=None,
    openapi_url="/openapi.json",  # Keep OpenAPI spec
    lifespan=lifespan,
)

# Apply custom Swagger UI documentation
customize_swagger_docs(app)

# ── Middleware stack (order matters: last added = first executed) ─────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware — logs every API call with timing
app.add_middleware(RequestLoggingMiddleware)


@app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
async def custom_swagger_ui_html():
    """Serve custom Swagger UI with manual token input"""
    return HTMLResponse(content=get_swagger_html())


@app.get("/", include_in_schema=False)
async def home_redirect():
    """Redirect root to documentation"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/v1/models", include_in_schema=False)
async def mock_models():
    """Mock endpoint to suppress 404 errors from AI tools/plugins"""
    return {
        "object": "list",
        "data": []
    }


app.include_router(api_router, prefix=settings.api_v1_prefix)
# swagger_login_router mounted at app level for /swagger/login to match OpenAPI spec
app.include_router(swagger_login_router, include_in_schema=False)
