from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes.companies import router as companies_router
from app.api.routes.query import router as query_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.upload import router as upload_router
from config import settings

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="FinbotAI Backend", version="0.1.0")

Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(companies_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")


@app.on_event("startup")
async def load_companies_file() -> None:
    from config import settings
    companies_path = Path(settings.COMPANIES_FILE)
    if not companies_path.exists():
        companies_path.write_text(json.dumps({"companies": [], "active_company": None}, indent=2), encoding="utf-8")
        return

    try:
        payload: dict[str, Any] = json.loads(companies_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {"companies": [], "active_company": None}
        companies_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Reset stuck processing jobs — ChromaDB is source of truth
    dirty = False
    for company in payload.get("companies", []):
        slug = company.get("slug", "unknown")
        collections = company.get("collections", {})
        if not isinstance(collections, dict):
            continue
        for file_type, collection in collections.items():
            if isinstance(collection, dict) and collection.get("status") == "processing":
                collection["status"] = "uploaded"
                dirty = True
                logger.warning(f"[Startup] Reset stuck status: {slug}/{file_type} processing → uploaded")
    if dirty:
        companies_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    app.state.companies_payload = payload
    app.state.settings = settings


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "FinbotAI backend is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
