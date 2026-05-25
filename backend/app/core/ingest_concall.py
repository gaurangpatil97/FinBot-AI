from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pdfplumber
from loguru import logger

from app.core.embedder import generate_embeddings
from app.db.vector_store import store_chunks


def ingest_single_concall(
    file_path: Path,
    company_slug: str,
    year: Optional[str],
    quarter: Optional[str],
    collection_name: str,
    chroma_path: str,
) -> list[dict]:
    """Speaker-aware concall ingestion for a single PDF."""
    filename = file_path.name
    logger.info(f"[Concall] Processing {filename} | {year} {quarter}")

    pages = _extract_text_by_page(str(file_path))
    all_chunks = []

    for page_data in pages:
        speaker_blocks = _parse_speaker_blocks(page_data["text"])
        if not speaker_blocks:
            all_chunks.append(_make_chunk(
                page_data["text"], filename,
                page_data["page"], 0,
                year, quarter, "text", "unknown", company_slug
            ))
            continue
        page_chunks = _build_qa_chunks(
            speaker_blocks, filename,
            page_data["page"], year, quarter, company_slug
        )
        all_chunks.extend(page_chunks)

    logger.info(f"[Concall] {len(all_chunks)} chunks — generating embeddings")
    all_chunks = generate_embeddings(all_chunks)
    store_chunks(all_chunks, collection_name, chroma_path=chroma_path)
    logger.success(f"[Concall] Stored {len(all_chunks)} chunks → {collection_name}")
    return all_chunks


def _extract_text_by_page(pdf_path: str) -> list[dict]:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages.append({"page": i, "text": text.strip()})
    return pages


def _parse_speaker_blocks(text: str) -> list[dict]:
    pattern = re.compile(r'^([A-Z][A-Za-z\s\.]+):\s+', re.MULTILINE)
    matches = list(pattern.finditer(text))
    blocks = []
    for i, match in enumerate(matches):
        speaker = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            blocks.append({
                "speaker": speaker,
                "content": content,
                "is_management": "srinivasan" in speaker.lower()
            })
    return blocks


def _build_qa_chunks(
    speaker_blocks: list[dict],
    filename: str,
    page: int,
    year: Optional[str],
    quarter: Optional[str],
    company_slug: str,
) -> list[dict]:
    chunks = []
    i = 0
    chunk_index = 0
    while i < len(speaker_blocks):
        block = speaker_blocks[i]
        if block["is_management"] and (i == 0 or speaker_blocks[i - 1]["is_management"]):
            content = f"Management Commentary:\n{block['content']}"
            chunks.append(_make_chunk(
                content, filename, page, chunk_index,
                year, quarter, "management_commentary",
                block["speaker"], company_slug
            ))
            chunk_index += 1
            i += 1
        elif not block["is_management"] and block["speaker"] != "Moderator":
            qa = f"Analyst ({block['speaker']}) asked:\n{block['content']}\n"
            if i + 1 < len(speaker_blocks) and speaker_blocks[i + 1]["is_management"]:
                qa += f"\nManagement answered:\n{speaker_blocks[i + 1]['content']}"
                i += 2
            else:
                i += 1
            chunks.append(_make_chunk(
                qa, filename, page, chunk_index,
                year, quarter, "qa_exchange",
                block["speaker"], company_slug
            ))
            chunk_index += 1
        else:
            i += 1
    return chunks


def _make_chunk(
    content: str, filename: str, page: int,
    chunk_index: int, year: Optional[str],
    quarter: Optional[str], chunk_type: str,
    speaker: str, company_slug: str
) -> dict:
    return {
        "content": content,
        "metadata": {
            "filename": filename,
            "page": page,
            "chunk_index": chunk_index,
            "chunk_type": chunk_type,
            "speaker": speaker,
            "quarter": quarter or "unknown",
            "year": year or "unknown",
            "company_slug": company_slug,
            "source_type": "concall",
        },
        "embedding": None,
    }
