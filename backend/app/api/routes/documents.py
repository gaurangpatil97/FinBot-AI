from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["documents"])


@router.get("/documents/{company_slug}", response_model=List[Dict[str, Any]])
def list_documents(company_slug: str) -> List[Dict[str, Any]]:
    companies_path = Path("companies.json")
    if not companies_path.exists():
        raise HTTPException(status_code=404, detail="No companies file found")

    payload = json.loads(companies_path.read_text(encoding="utf-8"))
    for company in payload.get("companies", []):
        if company.get("slug") == company_slug:
            return company.get("files", [])

    raise HTTPException(status_code=404, detail="Company not found")
