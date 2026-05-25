from __future__ import annotations

from typing import Any, Dict, List

import ollama
from loguru import logger

from app.core.build_prompt import build_prompt
from app.core.calculation_agent import try_calculation
from app.core.embedder import generate_embeddings
from app.core.router_agent import route_question
from app.db.vector_store import query_collection, query_collection_by_type
from app.models.schemas import Citation, QueryRequest, QueryResponse
from config import settings


def answer_query(request: QueryRequest) -> QueryResponse:
    question = request.question
    company_slug = request.company_slug
    year = request.year

    # Step 1 — Route the question
    decision = route_question(question, company_slug, year)
    source_types = decision.source_types
    routed_year = decision.year or year

    logger.info(f"[RAG] Routing to: {source_types} | Year: {routed_year}")

    # Step 2 — Try calculation agent first
    calc_result = try_calculation(question)
    if calc_result is not None:
        answer = f"{calc_result['answer']} (computed: {calc_result['formula_used']})"
        citations = [Citation(
            filename=f"{company_slug}_excel",
            page=calc_result.get("year", "computed"),
            collection=f"{company_slug}_excel"
        )]
        return QueryResponse(
            answer=answer,
            citations=citations,
            collections_searched=[f"{company_slug}_excel"],
            agent_used="calculation_agent",
            agent_trace=calc_result.get("trace", "")
        )

    # Step 3 — Embed the question
    query_chunks = [{"content": question, "metadata": {}, "embedding": None}]
    query_embedding = generate_embeddings(query_chunks)[0]["embedding"]

    # Step 4 — Retrieve chunks from routed collections
    all_chunks = []

    if "excel" in source_types:
        chunks = query_collection(
            query_embedding,
            f"{company_slug}_excel",
            year=routed_year,
            chroma_path=f"{settings.CHROMA_BASE_DIR}/{company_slug}/excel"
        )
        logger.info(f"Excel chunks: {len(chunks)}")
        all_chunks.extend(chunks)

    if "pdf" in source_types:
        chunks = query_collection(
            query_embedding,
            f"{company_slug}_pdf_text",
            year=routed_year,
            chroma_path=f"{settings.CHROMA_BASE_DIR}/{company_slug}/pdf"
        )
        logger.info(f"PDF text chunks: {len(chunks)}")
        all_chunks.extend(chunks)

    if "images" in source_types:
        chunks = query_collection_by_type(
            query_embedding,
            f"{company_slug}_images",
            chunk_type="image",
            year=None,
            top_k=4,
            chroma_path=f"{settings.CHROMA_BASE_DIR}/{company_slug}/images"
        )
        logger.info(f"Image chunks: {len(chunks)}")
        all_chunks.extend(chunks)

    if "concall" in source_types:
        chunks = query_collection(
            query_embedding,
            f"{company_slug}_concalls",
            year=None,
            chroma_path=f"{settings.CHROMA_BASE_DIR}/{company_slug}/concall"
        )
        logger.info(f"Concall chunks: {len(chunks)}")
        all_chunks.extend(chunks)

    # Step 5 — Rank and trim
    all_chunks = sorted(all_chunks, key=lambda x: x["score"], reverse=True)
    top_chunks = all_chunks[:settings.TOP_K_CHUNKS]

    if not top_chunks:
        return QueryResponse(
            answer="I could not find relevant information in the corpus. Please ensure embeddings have been generated.",
            citations=[],
            collections_searched=source_types,
            agent_used="rag",
            agent_trace="No chunks retrieved"
        )

    # Step 6 — Build prompt
    prompt = build_prompt(question, top_chunks)

    # Step 7 — Call Ollama
    logger.info(f"[RAG] Calling Ollama: {settings.OLLAMA_MODEL}")
    response = ollama.chat(
        model=settings.OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response["message"]["content"]

    # Step 8 — Build citations
    citations = []
    seen = set()
    for chunk in top_chunks:
        filename = chunk["metadata"].get("filename", "unknown")
        page = chunk["metadata"].get("page") or chunk["metadata"].get("sheet", "unknown")
        collection = chunk["metadata"].get("collection", "unknown")
        key = (filename, page)
        if key not in seen:
            seen.add(key)
            citations.append(Citation(
                filename=filename,
                page=page,
                collection=collection
            ))

    logger.success(f"[RAG] Answered with {len(citations)} citations")
    return QueryResponse(
        answer=answer,
        citations=citations,
        collections_searched=source_types,
        agent_used="rag",
        agent_trace="Full RAG pipeline"
    )