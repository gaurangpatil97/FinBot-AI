from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional

import openai
from loguru import logger

from config import get_settings

settings = get_settings()


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
    # Keep the fallback router source-agnostic so it does not encode one company's vocabulary.
    "quarterly", "investor call",
    "we expect", "company guided", "going forward",
]

EXCEL_KEYWORDS = [
    "revenue", "sales", "profit", "ebitda", "ebit", "pat", "pbt",
    "borrowings", "debt", "networth", "equity", "depreciation",
    "cash flow", "capex", "balance sheet", "return on", "roce", "roe",
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


def _keyword_route(question: str, company_slug: str, year: Optional[str] = None) -> RouteDecision:
    q = question.lower()

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


def route_question(
    question: str,
    company_slug: str,
    year: Optional[str] = None,
) -> RouteDecision:
    q = question.lower()

    extracted_year = year
    if not extracted_year:
        # Extract any FYXX or 20XX year dynamically so routing stays generic.
        match = re.search(r'\b(?:FY)?(20\d{2}|\d{2})\b', question, re.IGNORECASE)
        if match:
            extracted = match.group(1)
            extracted_year = f"20{extracted}" if len(extracted) == 2 else extracted

    prompt = f"""You are a financial data router. Given a question, decide which data sources to search.

    Available sources:
    - excel: structured financial data, precise numbers, 10 years of financials, ratios calculated from numbers
    - pdf: annual report narrative, strategy, MD&A, business segments, management discussion, chairman message, risk factors, product descriptions, operational framework
    - images: charts, graphs, visuals, infographics from annual report pages
    - concall: earnings call transcripts, management commentary, guidance, analyst Q&A

    Examples:
    # Neutral year placeholders — avoid benchmark phrasing bias
    Q: What was the revenue in FYxx? → {{"source_types": ["excel"], "year": "2022"}}
    Q: What is the company's operational strategy? → {{"source_types": ["pdf"], "year": null}}
    Q: Who is the chairman and what framework does he highlight? → {{"source_types": ["pdf"], "year": null}}
    Q: What are the risk factors mentioned in the annual report? → {{"source_types": ["pdf"], "year": null}}
    Q: What did management guide for next quarter? → {{"source_types": ["concall"], "year": null}}
    Q: Calculate the debt to equity ratio for FYxx? → {{"source_types": ["excel"], "year": "2023"}}
    Q: What segment has higher margins and why? → {{"source_types": ["pdf"], "year": null}}
    Q: Show me the revenue chart → {{"source_types": ["images"], "year": null}}
    Q: What was EBITDA margin trend from FYxx to FYyy? → {{"source_types": ["excel", "pdf"], "year": null}}
    Q: What was the revenue shown in the FYxx annual report? → {{'source_types': ['images', 'pdf'], 'year': '2022'}}
    Q: What percentage was shown in the annual report chart? → {{'source_types': ['images'], 'year': null}}
    Q: What was the market cap shown in FYxx annual report? → {{'source_types': ['images', 'pdf'], 'year': '2022'}}
    Q: What does the annual report show about segment revenue? → {{'source_types': ['images', 'pdf'], 'year': null}}
    Q: What was the ROCE shown in the annual report visuals? → {{'source_types': ['images'], 'year': null}}
    Q: How many plants shown in annual report? → {{'source_types': ['images', 'pdf'], 'year': null}}

Return ONLY a JSON object, no explanation, no markdown:
{{"source_types": ["pdf"], "year": "2022"}}

Question: {question}
"""

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        source_types = result.get("source_types", [])
        if not source_types:
            raise ValueError("empty source_types")
        routed_year = result.get("year") or extracted_year
        collections = [f"{company_slug}_{source_type}" for source_type in source_types]

        logger.info(f"[Router] LLM → {source_types} | Year: {routed_year}")

        return RouteDecision(
            source_types=source_types,
            year=routed_year,
            collections_searched=collections,
        )
    except Exception:
        logger.warning("[Router] LLM routing failed, falling back to keywords")
        return _keyword_route(question, company_slug, extracted_year)
