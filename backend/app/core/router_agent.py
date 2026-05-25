from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from loguru import logger


@dataclass
class RouteDecision:
    source_types: List[str]
    year: Optional[str]
    agent_used: str = "router"
    collections_searched: List[str] = field(default_factory=list)


CONCALL_KEYWORDS = [
    "management said", "management guided", "management mentioned",
    "management commentary", "management claimed", "management highlighted",
    "concall", "earnings call", "conference call",
    "what did", "guidance", "analyst asked",
    "forward guidance", "next quarter", "target", "commentary",
    "q1 fy", "q2 fy", "q3 fy", "q4 fy", "h1 fy", "h2 fy",
    "storage solutions", "capacity utilization", "capacity addition",
    "per month", "nine months", "quarterly", "investor call",
    "we expect", "company guided", "going forward",
]

EXCEL_KEYWORDS = [
    "revenue", "sales", "profit", "ebitda", "ebit", "pat", "pbt",
    "borrowings", "debt", "networth", "equity", "depreciation",
    "cash flow", "capex", "fy20", "fy21", "fy22", "fy23", "fy24",
    "fy25", "fy26", "balance sheet", "return on", "roce", "roe",
    "eps", "dividend", "interest", "working capital", "inventory",
]

IMAGE_KEYWORDS = [
    "chart", "graph", "image", "visual", "infographic", "pie chart",
    "shown in", "as shown", "depicted", "illustrated", "figure",
    "annual report shows", "annual report chart", "report image",
    "segment share", "segment breakdown",
]

PDF_KEYWORDS = [
    "strategy", "risk", "md&a", "annual report", "narrative",
    "business overview", "management discussion", "directors report",
    "industry", "competition", "regulatory", "description",
    "liquidity", "capital allocation", "esg", "workforce",
]

IMAGE_FORCE_TRIGGERS = [
    "shown in", "as shown in", "annual report shows",
    "annual report chart", "annual report visuals",
    "annual report image", "image pages", "visual pages",
]


def route_question(
    question: str,
    company_slug: str,
    year: Optional[str] = None,
) -> RouteDecision:
    q = question.lower()

    # Detect year from question if not provided
    if not year:
        match = re.search(r'\b(20\d{2})\b', question)
        year = match.group(1) if match else None

        # Also handle FY format
        fy_match = re.search(r'\bFY(\d{2,4})\b', question, re.IGNORECASE)
        if fy_match:
            fy = fy_match.group(1)
            year = f"20{fy}" if len(fy) == 2 else fy

    # Force image route
    if any(trigger in q for trigger in IMAGE_FORCE_TRIGGERS):
        logger.info(f"[Router] Force → image for: '{q[:60]}'")
        collections = [f"{company_slug}_images", f"{company_slug}_excel"]
        return RouteDecision(
            source_types=["images", "excel"],
            year=year,
            collections_searched=collections
        )

    # Score sources
    concall_score = sum(1 for kw in CONCALL_KEYWORDS if kw in q)
    excel_score   = sum(1 for kw in EXCEL_KEYWORDS   if kw in q)
    image_score   = sum(1 for kw in IMAGE_KEYWORDS   if kw in q)
    pdf_score     = sum(1 for kw in PDF_KEYWORDS      if kw in q)

    sources = []
    if concall_score >= 1:
        sources.append("concall")
    if excel_score >= 1:
        sources.append("excel")
    if image_score >= 1:
        sources.append("images")
    if pdf_score >= 1:
        sources.append("pdf")
    if not sources:
        sources = ["concall", "excel", "images", "pdf"]

    collections = [f"{company_slug}_{s}" for s in sources]

    logger.info(
        f"[Router] Scores — concall:{concall_score} excel:{excel_score} "
        f"image:{image_score} pdf:{pdf_score} → {sources}"
    )

    return RouteDecision(
        source_types=sources,
        year=year,
        collections_searched=collections
    )