from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.db.vector_store import get_persistent_client
from app.models.schemas import CompanyCreateRequest, CompanyStatus
from config import settings

router = APIRouter(tags=["companies"])
COMPANIES_FILE = Path(settings.COMPANIES_FILE)


def _read_companies_file() -> Dict[str, Any]:
    if not COMPANIES_FILE.exists():
        return {"companies": [], "active_company": None}
    return json.loads(COMPANIES_FILE.read_text(encoding="utf-8-sig"))


def _write_companies_file(payload: Dict[str, Any]) -> None:
    COMPANIES_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@router.get("/companies", response_model=List[dict])
def list_companies() -> List[dict]:
    payload = _read_companies_file()
    return payload.get("companies", [])


@router.post("/companies", response_model=dict)
def create_company(request: CompanyCreateRequest) -> dict:
    payload = _read_companies_file()
    companies = payload.setdefault("companies", [])

    if any(company.get("slug") == request.slug for company in companies):
        raise HTTPException(status_code=409, detail="Company already exists")

    record = {
        "name": request.name,
        "slug": request.slug,
        "ticker": request.ticker,
        "collections": {
            "excel": {"status": "no-embeddings", "chunks": 0},
            "pdf": {"status": "no-embeddings", "chunks": 0},
            "concall": {"status": "no-embeddings", "chunks": 0},
            "images": {"status": "no-embeddings", "chunks": 0},
        },
        "files": [],
    }
    companies.append(record)
    payload["active_company"] = request.slug
    _write_companies_file(payload)
    return record


@router.get("/companies/{slug}/status")
def get_company_status(slug: str) -> dict:
    payload = _read_companies_file()
    company = next((item for item in payload.get("companies", []) if item.get("slug") == slug), None)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    import chromadb

    collections: Dict[str, Dict[str, int | str]] = {}
    collection_map = [
        ("excel", f"{slug}_excel"),
        ("pdf", f"{slug}_pdf_text"),
        ("concall", f"{slug}_concalls"),
        ("images", f"{slug}_images"),
    ]

    for col_type, collection_name in collection_map:
        chroma_path = str(Path(settings.CHROMA_BASE_DIR) / slug / col_type)
        try:
            client = get_persistent_client(chroma_path)
            collection = client.get_collection(collection_name)
            count = collection.count()
            collections[col_type] = {
                "status": "ready" if count > 0 else "no-embeddings",
                "chunks": count,
            }
        except Exception as e:
            from loguru import logger
            logger.error(f"ChromaDB error for {col_type}: {e}")
            collections[col_type] = {"status": "no-embeddings", "chunks": 0}

    return {
        "name": company["name"],
        "slug": company["slug"],
        "ticker": company["ticker"],
        "collections": collections,
    }


@router.get("/companies/{slug}/files")
def get_company_files(slug: str) -> dict:
    """Returns per-file chunk counts from ChromaDB metadata."""
    payload = _read_companies_file()
    if not any(company.get("slug") == slug for company in payload.get("companies", [])):
        raise HTTPException(status_code=404, detail="Company not found")

    import chromadb

    result: Dict[str, Dict[str, Dict[str, str | int | None]]] = {}
    collection_map = {
        "excel": f"{slug}_excel",
        "pdf": f"{slug}_pdf_text",
        "concall": f"{slug}_concalls",
        "images": f"{slug}_images",
    }

    for col_type, collection_name in collection_map.items():
        chroma_path = str(Path(settings.CHROMA_BASE_DIR) / slug / col_type)

        try:
            client = get_persistent_client(chroma_path)
            collection = client.get_collection(collection_name)
            data = collection.get(include=["metadatas"])
            metadatas = data.get("metadatas", []) if isinstance(data, dict) else []
            file_counts: Dict[str, Dict[str, str | int | None]] = {}

            for metadata in metadatas:
                if not isinstance(metadata, dict):
                    continue

                filename = metadata.get("filename")
                if not isinstance(filename, str) or not filename.strip():
                    filename = "unknown"

                entry = file_counts.setdefault(filename, {"chunks": 0, "year": None, "quarter": None})
                entry["chunks"] = int(entry["chunks"] or 0) + 1

                year = metadata.get("year")
                if entry["year"] is None and isinstance(year, str) and year.strip() and year != "unknown":
                    entry["year"] = year.strip()

                quarter = metadata.get("quarter")
                if entry["quarter"] is None and isinstance(quarter, str) and quarter.strip() and quarter != "unknown":
                    entry["quarter"] = quarter.strip()

            result[col_type] = file_counts
        except Exception:
            result[col_type] = {}

    return result
