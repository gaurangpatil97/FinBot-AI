from __future__ import annotations

from typing import Any, Dict, List

import openai
from loguru import logger

from app.core.build_prompt import build_prompt
from app.core.calculation_agent import try_calculation
from app.core.embedder import generate_embeddings
from app.core.router_agent import route_question
from app.db.vector_store import query_collection, query_collection_by_type
from app.models.schemas import Citation, QueryRequest, QueryResponse
from config import settings


def build_calculation_context(calc_result: dict, company_slug: str) -> list[dict]:
    if isinstance(calc_result, dict) and calc_result.get("multi_year"):
        metric_name = calc_result.get("metric_name", "unknown")
        results = calc_result.get("results", [])

        lines = [
            "Computation type: multi-year lookup",
            f"Metric: {metric_name}",
            "Year-wise answers:"
        ]

        for item in results:
            if not isinstance(item, dict):
                continue
            year = item.get("year", "unknown")
            answer = item.get("answer", "unknown")
            formula_used = item.get("formula_used", "")
            values_used = item.get("values_used", {})
            lines.append(f"- FY{year}: {answer}")
            if formula_used:
                lines.append(f"  Formula: {formula_used}")
            if values_used:
                lines.append(f"  Values: {values_used}")

        year_value = results[-1].get("year", "computed") if results and isinstance(results[-1], dict) else "computed"
        return [
            {
                "content": "\n".join(lines),
                "metadata": {
                    "filename": f"{company_slug}_excel",
                    "sheet": "calculation",
                    "year": year_value,
                },
            }
        ]

    metrics_used = calc_result.get("metrics_used", []) if isinstance(calc_result, dict) else []
    formula_used = calc_result.get("formula_used", "") if isinstance(calc_result, dict) else ""
    computation_type = calc_result.get("computation_type", "derived") if isinstance(calc_result, dict) else "derived"
    year = calc_result.get("year", "computed") if isinstance(calc_result, dict) else "computed"

    lines = [
        f"Computation type: {computation_type}",
        f"Formula used: {formula_used}",
        "Metric values used:",
    ]

    for metric in metrics_used:
        if not isinstance(metric, dict):
            continue
        name = metric.get("name", "unknown")
        sheet = metric.get("sheet", "unknown")
        metric_year = metric.get("year", "unknown")
        value = metric.get("value", "unknown")
        lines.append(f"- {name} ({sheet}, FY{metric_year}): {value}")

    return [
        {
            "content": "\n".join(lines),
            "metadata": {
                "filename": f"{company_slug}_excel",
                "sheet": "calculation",
                "year": year,
            },
        }
    ]


def normalize_pdf_year(routed_year: str | None) -> str | None:
    if isinstance(routed_year, list):
        routed_year = routed_year[0] if routed_year else None
    if routed_year is None:
        return None
    if routed_year.startswith("FY"):
        return routed_year
    if len(routed_year) == 4 and routed_year.isdigit():
        return f"FY{routed_year[-2:]}"
    return routed_year


def answer_query(request: QueryRequest) -> QueryResponse:
    question = request.question
    company_slug = request.company_slug
    year = request.year

    # Step 1 — Route the question
    decision = route_question(question, company_slug, year)
    source_types = decision.source_types
    routed_year = decision.year or year
    routed_year = routed_year[0] if isinstance(routed_year, list) and routed_year else routed_year

    logger.info(f"[RAG] Routing to: {source_types} | Year: {routed_year}")

    # Step 2 — Try calculation agent first
    calc_result = try_calculation(question, company_slug)
    if calc_result is not None:
        calc_context = build_calculation_context(calc_result, company_slug)
        prompt = build_prompt(question, calc_context, mode="calc")

        logger.info(f"[RAG] Calling OpenAI gpt-4o-mini for calculation response")
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        answer = response.choices[0].message.content.strip()

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
        pdf_year = normalize_pdf_year(routed_year)
        chunks = query_collection(
            query_embedding,
            f"{company_slug}_pdf_text",
            year=pdf_year,
            chroma_path=f"{settings.CHROMA_BASE_DIR}/{company_slug}/pdf"
        )
        logger.info(f"PDF text chunks: {len(chunks)}")
        all_chunks.extend(chunks)

    if "images" in source_types:
        image_year = normalize_pdf_year(routed_year)
        chunks = query_collection_by_type(
            query_embedding,
            f"{company_slug}_images",
            chunk_type="image",
            year=image_year,
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
    logger.info(f"[RAG] Calling OpenAI gpt-4o-mini for RAG response")
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    answer = response.choices[0].message.content.strip()

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