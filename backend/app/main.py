import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.paznic.vault import vault
from app.api import admin, arena, cases, rules, system
from app.config import settings
from app.core.store import store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

@asynccontextmanager
async def lifespan(_app):
    store.load()
    vault.load_into_gate()  # poarta anti-PII cunoaște valorile dosarelor existente și după restart
    yield


docs = settings.env != "demo"
app = FastAPI(
    title="ORB",
    lifespan=lifespan,
    docs_url="/docs" if docs else None,
    redoc_url=None,
    openapi_url="/openapi.json" if docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(admin.router)
app.include_router(system.router)
app.include_router(arena.router)
app.include_router(rules.router)


@app.get("/health")
def health():
    return {"status": "ok"}
