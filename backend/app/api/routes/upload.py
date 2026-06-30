from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from loguru import logger

from app.core.ingestor import ingest_uploaded_file, get_collection_name, get_chroma_path
from app.db.vector_store import get_persistent_client
from app.models.schemas import EmbedResponse, UploadResponse
from config import settings

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    company_slug: str = Form(...),
    file_type: str = Form(...),
    year: str | None = Form(default=None),
    quarter: str | None = Form(default=None),
) -> UploadResponse:
    if file_type not in {"excel", "pdf", "concall"}:
        raise HTTPException(status_code=400, detail="file_type must be excel, pdf, or concall")

    # Save file to disk
    upload_dir = Path(settings.BASE_UPLOAD_DIR) / company_slug / file_type
    upload_dir.mkdir(parents=True, exist_ok=True)
    original_filename = Path(file.filename).name
    destination = upload_dir / original_filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_id = str(uuid4())

    # Update companies.json with file record
    companies_path = Path(settings.COMPANIES_FILE)
    try:
        payload = json.loads(companies_path.read_text(encoding="utf-8"))
    except Exception:
        payload = {"companies": [], "active_company": None}

    for company in payload.get("companies", []):
        if company.get("slug") != company_slug:
            continue
        company.setdefault("files", []).append({
            "file_id": file_id,
            "filename": original_filename,
            "file_type": file_type,
            "year": year,
            "quarter": quarter,
            "status": "uploaded",
            "chunks": 0,
            "path": str(destination),
        })
        break

    companies_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info(f"[Upload] Saved {original_filename} → {destination}")

    return UploadResponse(
        file_id=file_id,
        filename=original_filename,
        company_slug=company_slug,
        file_type=file_type,
        status="uploaded",
    )


@router.post("/embed/{company_slug}", response_model=EmbedResponse)
async def generate_embeddings(
    company_slug: str,
    background_tasks: BackgroundTasks,
    images_only: bool = False,
) -> EmbedResponse:
    """
    Trigger embedding generation for all uploaded files for a company.
    Runs in background so frontend gets immediate response.
    """
    companies_path = Path(settings.COMPANIES_FILE)
    try:
        payload = json.loads(companies_path.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=404, detail="companies.json not found")

    company = next(
        (c for c in payload.get("companies", []) if c.get("slug") == company_slug),
        None
    )
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company '{company_slug}' not found")

    files = company.get("files", [])
    if not files:
        raise HTTPException(status_code=400, detail="No uploaded files pending embedding")

    # Mark all relevant collections as processing before queueing ingestion
    if "collections" in company:
        for file_type in set(f["file_type"] for f in files):
            if file_type in company["collections"]:
                company["collections"][file_type]["status"] = "processing"

    for f in company.get("files", []):
        if images_only:
            if f.get("status") in ("uploaded", "ready", "error", "pending"):
                f["status"] = "processing"
        else:
            if f.get("status") in ("uploaded", "error", "pending"):
                f["status"] = "processing"
    companies_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Run ingestion in background
    background_tasks.add_task(_run_ingestion, company_slug, files, images_only)

    return EmbedResponse(
        status="processing",
        chunks_created=0,
        collection_name=f"{company_slug}_all",
    )


def _run_ingestion(company_slug: str, files: list[dict], images_only: bool = False) -> None:
    """Background task — runs ingestor for each pending file."""
    for file_record in files:
        try:
            file_type = file_record["file_type"]
            filename = file_record["filename"]
            status = file_record.get("status", "")
            
            if images_only:
                if file_type != "pdf":
                    logger.info(f"Skipping {filename} — images_only mode, not a PDF")
                    continue
                if not any(p in filename for p in settings.IMAGE_EMBED_FILENAME_PATTERNS):
                    logger.info(f"Skipping {filename} — no matching image pattern")
                    continue
            else:
                if status == "ready":
                    logger.info(f"Skipping {filename} — already processed (status: ready)")
                    continue
                if status not in ("processing", "pending", "uploaded", "error"):
                    logger.info(f"Skipping {filename} — status is {status}")
                    continue

            file_images_only = images_only if file_type == "pdf" else False
            result = ingest_uploaded_file(
                company_slug=company_slug,
                file_type=file_type,
                file_path=Path(file_record["path"]),
                year=file_record.get("year"),
                quarter=file_record.get("quarter"),
                images_only=file_images_only,
            )
            logger.success(f"[Embed] {file_record['filename']} → {result.chunks_created} chunks")

            # Update status to ready
            _update_file_status(company_slug, file_record["file_id"], "ready", result.chunks_created)

        except Exception as e:
            logger.error(f"[Embed] Failed for {file_record['filename']}: {e}")
            _update_file_status(company_slug, file_record["file_id"], "error", 0)


def _update_file_status(company_slug: str, file_id: str, status: str, chunks: int | None = None) -> None:
    companies_path = Path(settings.COMPANIES_FILE)
    try:
        payload = json.loads(companies_path.read_text(encoding="utf-8"))
        for company in payload.get("companies", []):
            if company.get("slug") != company_slug:
                continue
            for f in company.get("files", []):
                if f.get("file_id") == file_id:
                    f["status"] = status
                    if chunks is not None:
                        f["chunks"] = chunks
                    break
        companies_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"[Status update] Failed: {e}")


def reconcile_stuck_statuses() -> None:
    companies_path = Path(settings.COMPANIES_FILE)
    try:
        payload = json.loads(companies_path.read_text(encoding="utf-8"))
    except Exception:
        return

    logger.info("[Reconcile] Checking stuck files...")
    fixed_ready = 0
    fixed_error = 0

    for company in payload.get("companies", []):
        company_slug = company.get("slug")
        if not company_slug:
            continue

        for file_record in company.get("files", []):
            if file_record.get("status") == "processing":
                try:
                    file_type = file_record["file_type"]
                    filename = file_record["filename"]
                    file_id = file_record["file_id"]

                    collection_name = get_collection_name(company_slug, file_type)
                    chroma_path = get_chroma_path(company_slug, file_type)
                    
                    client = get_persistent_client(chroma_path)
                    try:
                        collection = client.get_collection(collection_name)
                        # Filter by filename so we only count chunks for THIS specific file
                        result = collection.get(where={"filename": filename}, include=["metadatas"])
                        count = len(result.get("metadatas", []))
                    except Exception:
                        # Collection doesn't exist yet, meaning zero chunks
                        count = 0

                    if count > 0:
                        _update_file_status(company_slug, file_id, "ready", count)
                        fixed_ready += 1
                    else:
                        _update_file_status(company_slug, file_id, "error", 0)
                        fixed_error += 1
                except Exception as e:
                    logger.error(f"[Reconcile] Failed to check file {file_record.get('filename')}: {e}")

    if fixed_ready > 0 or fixed_error > 0:
        logger.info(f"[Reconcile] Fixed {fixed_ready + fixed_error} files: {fixed_ready} ready, {fixed_error} error")