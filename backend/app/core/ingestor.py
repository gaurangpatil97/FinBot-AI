from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger
from config import settings

from app.core.excel_processor import extract_excel
from app.core.pdf_processor import extract_pdf, extract_images_from_pdf
from app.core.chunker import chunk_documents
from app.core.embedder import generate_embeddings
from app.db.vector_store import store_chunks

COMPANIES_FILE = Path("companies.json")


@dataclass
class IngestionResult:
    company_slug: str
    file_type: str
    collection_name: str
    chunks_created: int
    status: str


def get_collection_name(company_slug: str, file_type: str) -> str:
    mapping = {
        "excel":   f"{company_slug}_excel",
        "pdf":     f"{company_slug}_pdf_text",
        "images":  f"{company_slug}_images",
        "concall": f"{company_slug}_concalls",
    }
    return mapping.get(file_type, f"{company_slug}_{file_type}")


def get_chroma_path(company_slug: str, file_type: str) -> str:
    return str(Path(settings.CHROMA_BASE_DIR) / company_slug / file_type)


def ingest_uploaded_file(
    company_slug: str,
    file_type: str,
    file_path: Path,
    year: Optional[str] = None,
    quarter: Optional[str] = None,
) -> IngestionResult:
    logger.info(f"[Ingestor] {file_type} | {file_path.name} | {company_slug}")

    filename = file_path.name
    total_chunks = 0
    main_collection = get_collection_name(company_slug, file_type)

    if file_type == "excel":
        pages = extract_excel(str(file_path))
        # Override collection and chroma path to be company-specific
        chunks = chunk_documents(pages)
        chunks = _tag_chunks(chunks, company_slug, filename, year=year)
        chunks = generate_embeddings(chunks)
        store_chunks(
            chunks,
            main_collection,
            chroma_path=get_chroma_path(company_slug, "excel")
        )
        total_chunks = len(chunks)

    elif file_type == "pdf":
        # Text pipeline
        text_pages = extract_pdf(str(file_path))
        text_chunks = chunk_documents(text_pages)
        text_chunks = _tag_chunks(text_chunks, company_slug, filename, year=year)
        text_chunks = generate_embeddings(text_chunks)
        store_chunks(
            text_chunks,
            get_collection_name(company_slug, "pdf"),
            chroma_path=get_chroma_path(company_slug, "pdf")
        )
        total_chunks += len(text_chunks)
        logger.info(f"PDF text: {len(text_chunks)} chunks stored")

        # Image pipeline — same PDF, processed via GPT-4o
        image_pages = extract_images_from_pdf(str(file_path))
        if image_pages:
            image_chunks = chunk_documents(image_pages)
            image_chunks = _tag_chunks(image_chunks, company_slug, filename, year=year)
            image_chunks = generate_embeddings(image_chunks)
            store_chunks(
                image_chunks,
                get_collection_name(company_slug, "images"),
                chroma_path=get_chroma_path(company_slug, "images")
            )
            total_chunks += len(image_chunks)
            logger.info(f"PDF images: {len(image_chunks)} chunks stored")

    elif file_type == "concall":
        from app.core.ingest_concall import ingest_single_concall
        chunks = ingest_single_concall(
            file_path=file_path,
            company_slug=company_slug,
            year=year,
            quarter=quarter,
            collection_name=main_collection,
            chroma_path=get_chroma_path(company_slug, "concall")
        )
        total_chunks = len(chunks)

    # Update companies.json
    update_company_index(company_slug, file_type, total_chunks)

    logger.success(f"[Ingestor] Done — {total_chunks} chunks for {company_slug}/{file_type}")
    return IngestionResult(
        company_slug=company_slug,
        file_type=file_type,
        collection_name=main_collection,
        chunks_created=total_chunks,
        status="ready"
    )


def _tag_chunks(
    chunks: list[dict],
    company_slug: str,
    filename: str,
    year: Optional[str] = None,
) -> list[dict]:
    """Add company_slug, filename, year to every chunk's metadata."""
    for chunk in chunks:
        chunk["metadata"]["company_slug"] = company_slug
        chunk["metadata"]["filename"] = filename
        if year:
            chunk["metadata"]["year"] = year
    return chunks


def update_company_index(
    company_slug: str,
    file_type: str,
    chunks_created: int
) -> None:
    """Update companies.json with embedding status and chunk count."""
    try:
        data = json.loads(COMPANIES_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {"companies": [], "active_company": None}

    company = next(
        (c for c in data["companies"] if c["slug"] == company_slug), None
    )
    if company is None:
        return

    if "collections" not in company:
        company["collections"] = {}

    existing = company["collections"].get(file_type, {})
    company["collections"][file_type] = {
        "status": "ready",
        "chunks": existing.get("chunks", 0) + chunks_created,
    }

    COMPANIES_FILE.write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    logger.info(f"[companies.json] {company_slug}/{file_type} → ready, {chunks_created} chunks")
