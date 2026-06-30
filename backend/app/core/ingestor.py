from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger
from config import settings

from app.core.excel_processor import extract_excel
from app.core.pdf_processor import extract_pdf, extract_images_from_pdf
from app.core.chunker import chunk_documents
from app.core.embedder import generate_embeddings
from app.db.vector_store import get_or_create_collection, store_chunks

COMPANIES_FILE = Path(settings.COMPANIES_FILE)


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
    images_only: bool = False,
) -> IngestionResult:
    logger.info(f"[Ingestor] {file_type} | {file_path.name} | {company_slug} | images_only={images_only}")

    filename = file_path.name
    total_chunks = 0
    main_collection = get_collection_name(company_slug, file_type)

    if images_only and file_type == "pdf":
        logger.info(f"Running images-only mode for {filename} — skipping text extraction")
        # Delete existing chunks in the images collection for this file
        images_col_name = get_collection_name(company_slug, "images")
        try:
            images_collection = get_or_create_collection(
                images_col_name,
                chroma_path=get_chroma_path(company_slug, "images")
            )
            images_collection.delete(where={"filename": filename})
        except Exception as exc:
            logger.warning(f"Could not clear images collection for {filename}: {exc}")
    else:
        # Check if collection already has data
        collection = get_or_create_collection(
            main_collection,
            chroma_path=get_chroma_path(company_slug, file_type)
        )
        existing_count = collection.count()
        if existing_count > 0:
            logger.warning(f"[Ingestor] Collection {main_collection} already has {existing_count} chunks — overwriting")
            collection.delete(where={"filename": file_path.name})

    if file_type == "excel":
        pages = extract_excel(str(file_path))
        # Override collection and chroma path to be company-specific
        chunks = chunk_documents(pages)
        chunks = _tag_chunks(chunks, company_slug, filename, year=year)
        chunks = generate_embeddings(chunks)
        extract_and_store_kpis(file_path, company_slug)
        store_chunks(
            chunks,
            main_collection,
            chroma_path=get_chroma_path(company_slug, "excel")
        )
        total_chunks = len(chunks)
        update_company_index(company_slug, file_type, total_chunks, status="ready")

    elif file_type == "pdf":
        if not images_only:
            # Text pipeline
            try:
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
                update_company_index(company_slug, "pdf", len(text_chunks), status="ready")
            except Exception as exc:
                logger.error(f"PDF text pipeline failed for {filename}: {exc}")
                update_company_index(company_slug, "pdf", 0, status="error")

        # Image pipeline — same PDF, processed via GPT-4o
        try:
            should_embed_images = False
            if settings.ENABLE_IMAGE_EMBEDDING:
                has_pattern = any(pattern in filename for pattern in settings.IMAGE_EMBED_FILENAME_PATTERNS)
                if has_pattern:
                    should_embed_images = True
                else:
                    logger.info(f"Skipping image embedding for {filename} — no matching pattern")
            
            if should_embed_images:
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
                    update_company_index(company_slug, "images", len(image_chunks), status="ready")
                else:
                    update_company_index(company_slug, "images", 0, status="no-embeddings")
            else:
                update_company_index(company_slug, "images", 0, status="no-embeddings")
        except Exception as exc:
            logger.error(f"PDF image pipeline failed for {filename}: {exc}")
            update_company_index(company_slug, "images", 0, status="error")

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
        update_company_index(company_slug, file_type, total_chunks, status="ready")

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


def extract_and_store_kpis(file_path: Path, company_slug: str) -> None:
    # Unit detected at embed time — not hardcoded at query time
    try:
        df = pd.read_excel(file_path, sheet_name="Data Sheet", header=None)
    except Exception as exc:
        logger.warning(f"[Ingestor] KPI extraction skipped for {file_path.name}: {exc}")
        return

    report_date_idx = None
    for idx, row in df.iterrows():
        first_cell = str(row.iloc[0]).strip().lower() if len(row) > 0 and pd.notna(row.iloc[0]) else ""
        if first_cell == "report date":
            report_date_idx = idx
            break

    if report_date_idx is None:
        return

    header_row = df.iloc[report_date_idx]
    year_cols: list[tuple[str, int]] = []
    for col_idx, val in enumerate(header_row.iloc[1:], start=1):
        if pd.isna(val):
            continue
        try:
            dt = val if hasattr(val, "year") else pd.to_datetime(val)
            fiscal_year = dt.year + 1 if dt.month >= 4 else dt.year
            year_cols.append((str(fiscal_year), col_idx))
        except Exception:
            continue

    def _detect_unit(metric_values: list[float]) -> str:
        if metric_values:
            avg_value = sum(metric_values) / len(metric_values)
            if avg_value > 100000:
                return "M"
            if avg_value > 100:
                return "Cr"
        for col_idx, value in year_cols:
            if isinstance(value, str) and "$" in value:
                return "$"
        return "Cr"

    metric_rows = []
    for section, sheet_name, label in [
        ("PROFIT & LOSS", "profit_loss", "Sales"),
        ("BALANCE SHEET", "balance_sheet", "Borrowings"),
        ("CASH FLOW:", "cash_flow", "Cash from Operating Activity"),
    ]:
        start_idx = None
        end_idx = None
        for idx, row in df.iterrows():
            first_cell = str(row.iloc[0]).strip().lower() if len(row) > 0 and pd.notna(row.iloc[0]) else ""
            if first_cell == section.lower():
                start_idx = idx
            elif start_idx is not None and first_cell in {"quarters", "cash flow:"}:
                end_idx = idx
                break
        if start_idx is None:
            continue
        segment = df.iloc[start_idx + 1:end_idx if end_idx is not None else len(df)]
        for idx, row in segment.iterrows():
            metric_name = str(row.iloc[0]).strip()
            if not metric_name or metric_name.lower() == "nan":
                continue
            values = []
            for year, col_idx in year_cols:
                raw_value = row.iloc[col_idx] if col_idx < len(row) else None
                if pd.isna(raw_value):
                    continue
                if isinstance(raw_value, (int, float)):
                    values.append(float(raw_value))
            if not values:
                continue
            metric_rows.append((sheet_name, metric_name, values, {year: row.iloc[col_idx] for year, col_idx in year_cols if col_idx < len(row) and pd.notna(row.iloc[col_idx])}))

    try:
        data = json.loads(COMPANIES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return

    company = next((c for c in data.get("companies", []) if c.get("slug") == company_slug), None)
    if company is None:
        return

    company.setdefault("kpis", {})
    for sheet_name, metric_name, values, year_values in metric_rows:
        company["kpis"].setdefault(metric_name, {})
        company["kpis"][metric_name]["unit"] = _detect_unit(values)
        company["kpis"][metric_name]["values"] = year_values

    COMPANIES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def update_company_index(
    company_slug: str,
    file_type: str,
    chunks_created: int,
    status: str = "ready"
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

    collection_name = get_collection_name(company_slug, file_type)
    collection = get_or_create_collection(
        collection_name,
        chroma_path=get_chroma_path(company_slug, file_type),
    )
    actual_chunk_count = collection.count()

    company["collections"][file_type] = {
        "status": status,
        "chunks": actual_chunk_count,
    }

    COMPANIES_FILE.write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    logger.info(f"[companies.json] {company_slug}/{file_type} → {status}, {actual_chunk_count} chunks")
