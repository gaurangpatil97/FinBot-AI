from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.models.schemas import CompanyCreateRequest, CompanyStatus

router = APIRouter(tags=["companies"])
COMPANIES_FILE = Path("companies.json")


def _read_companies_file() -> Dict[str, Any]:
    if not COMPANIES_FILE.exists():
        return {"companies": [], "active_company": None}
    return json.loads(COMPANIES_FILE.read_text(encoding="utf-8"))


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


@router.get("/companies/{slug}/status", response_model=CompanyStatus)
def get_company_status(slug: str) -> CompanyStatus:
    payload = _read_companies_file()
    for company in payload.get("companies", []):
        if company.get("slug") == slug:
            return CompanyStatus(**company)
    raise HTTPException(status_code=404, detail="Company not found")
