from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, engine, import_models

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import_models()
    yield
    await engine.dispose()


app = FastAPI(
    title="Sàn Dịch Vụ API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
async def health_db() -> dict[str, str]:
    import_models()
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


app.include_router(api_router, prefix=settings.api_v1_prefix)
