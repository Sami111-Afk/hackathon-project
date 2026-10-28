from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

docs = settings.env != "demo"
app = FastAPI(
    title="ORB",
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


@app.get("/health")
def health():
    return {"status": "ok", "llm_mode": settings.llm_mode}
