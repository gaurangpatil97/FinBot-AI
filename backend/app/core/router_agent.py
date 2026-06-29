from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional

import openai
from loguru import logger
import time

from config import get_settings
from app.core.metrics import OPENAI_CALL_LATENCY, OPENAI_CALL_COUNT

settings = get_settings()


@dataclass
class RouteDecision:
    source_types: List[str]
    year: Optional[str]
    agent_used: str = "router"
    collections_searched: List[str] = field(default_factory=list)
    sheet: Optional[str] = None


CONCALL_KEYWORDS = [
    "management said", "management guided", "management mentioned",
    "management commentary", "management claimed", "management highlighted",
    "concall", "earnings call", "conference call",
    "what did", "guidance", "analyst asked",
    "forward guidance", "next quarter", "target", "commentary",
    "q1 fy", "q2 fy", "q3 fy", "q4 fy", "h1 fy", "h2 fy",
    # Keep the fallback router source-agnostic so it does not encode one company's vocabulary.
    "quarterly", "investor call", "half year", "first half", "second half",
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
    "bar chart", "donut chart", "kpi chart", "kpi page", "table",
    "shown in", "shown in the", "as shown", "displays", "depicts", "depicted", "illustrated", "figure",
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
    "annual report image", "image pages", "visual pages", "table",
]


def _keyword_route(question: str, company_slug: str, year: Optional[str] = None) -> RouteDecision:
    q = question.lower()

    detected_sheet = None
    if "balance sheet" in q or "balance_sheet" in q:
        detected_sheet = "balance_sheet"
    elif "cash flow" in q or "cash_flow" in q or "cashflow" in q:
        detected_sheet = "cash_flow"
    elif "profit" in q or "loss" in q or "p&l" in q or "p and l" in q or "income statement" in q:
        detected_sheet = "profit_loss"

    # Force image route
    if any(trigger in q for trigger in IMAGE_FORCE_TRIGGERS):
        logger.info(f"[Router] Force → image for: '{q[:60]}'")
        collections = [f"{company_slug}_images", f"{company_slug}_excel"]
        return RouteDecision(
            source_types=["images", "excel"],
            year=year,
            agent_used="keyword_fallback",
            collections_searched=collections,
            sheet=detected_sheet
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
        agent_used="keyword_fallback",
        collections_searched=collections,
        sheet=detected_sheet
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

    prompt = f"""You are a financial data router. Given a question, decide which data sources to search and if a specific financial sheet/statement is targeted.
    If the question targets a specific financial sheet (e.g., profit_loss, balance_sheet, cash_flow, etc.), identify that sheet name dynamically (lowercase with underscores) and return it under the 'sheet' key. Otherwise return null.

    Available sources:
    - excel: structured financial data, precise numbers, 10 years of financials, ratios calculated from numbers
    - pdf: annual report narrative, strategy, MD&A text, business segments, management discussion, chairman message, risk factors, product descriptions, operational framework
    - images: charts, graphs, tables, visuals, infographics from annual report pages (even if they appear within MD&A or BRSR sections)
    - concall: earnings call transcripts, management commentary, guidance, analyst Q&A

    Key routing rules:
    - If the question asks to verify, cross-check, or compare information across different document types (e.g. comparing what management said in an earnings call against figures reported in the annual report or financial statements), you MUST route to ALL relevant sources simultaneously.
    - Questions containing words like "verify", "confirm", "cross-check", "reconcile", "management claimed", "actual vs guided", "did the company achieve" are strong signals for multi-source routing.
    - When in doubt between single-source and multi-source, prefer multi-source.
    - H1, H2, Q1, Q2, Q3, Q4, quarterly, half-year → concall
    - bar chart, donut chart, KPI chart, infographic, visual, table → images
    - MD&A, BRSR, auditor, KAM, Directors Report → pdf (Note: if asking about a TABLE or CHART within these sections, route to images instead)
    - specific numbers, ratios, calculations → excel
    - When question asks about something shown or displayed visually or in a table → images

    Examples:
    # Neutral year placeholders — avoid benchmark phrasing bias
    Q: What was the revenue in FYxx? → {{"source_types": ["excel"], "year": "2022", "sheet": "profit_loss"}}
    Q: What is the company's operational strategy? → {{"source_types": ["pdf"], "year": null, "sheet": null}}
    Q: Who is the chairman and what framework does he highlight? → {{"source_types": ["pdf"], "year": null, "sheet": null}}
    Q: What are the risk factors mentioned in the annual report? → {{"source_types": ["pdf"], "year": null, "sheet": null}}
    Q: What did management guide for next quarter? → {{"source_types": ["concall"], "year": null, "sheet": null}}
    Q: Calculate the debt to equity ratio for FYxx? → {{"source_types": ["excel"], "year": "2023", "sheet": "balance_sheet"}}
    Q: What segment has higher margins and why? → {{"source_types": ["pdf"], "year": null, "sheet": null}}
    Q: Show me the revenue chart → {{"source_types": ["images"], "year": null, "sheet": null}}
    Q: What was EBITDA margin trend from FYxx to FYyy? → {{"source_types": ["excel", "pdf"], "year": null, "sheet": "profit_loss"}}
    Q: What was the revenue shown in the FYxx annual report? → {{'source_types': ['images', 'pdf'], 'year': '2022', 'sheet': 'profit_loss'}}
    Q: What percentage was shown in the annual report chart? → {{'source_types': ['images'], 'year': null, 'sheet': null}}
    Q: What was the market cap shown in FYxx annual report? → {{'source_types': ['images', 'pdf'], 'year': '2022', 'sheet': 'balance_sheet'}}
    Q: What does the annual report show about segment revenue? → {{'source_types': ['images', 'pdf'], 'year': null, 'sheet': null}}
    Q: What was the ROCE shown in the annual report visuals? → {{'source_types': ['images'], 'year': null, 'sheet': null}}
    Q: How many plants shown in annual report? → {{'source_types': ['images', 'pdf'], 'year': null, 'sheet': null}}
    Q: What was H1 revenue as disclosed by management? → {{"source_types": ["concall"], "year": null, "sheet": null}}
    Q: What did management say in Q1 about margins? → {{"source_types": ["concall"], "year": null, "sheet": null}}
    Q: What was the quarterly EBIT for each segment? → {{"source_types": ["concall"], "year": null, "sheet": null}}
    Q: Compare H1 vs H2 performance? → {{"source_types": ["concall"], "year": null, "sheet": null}}
    Q: What is shown in the KPI bar chart? → {{"source_types": ["images"], "year": null, "sheet": null}}
    Q: What does the donut chart show for segment revenue? → {{"source_types": ["images"], "year": null, "sheet": null}}
    Q: What trend is visible in the bar chart? → {{"source_types": ["images"], "year": null, "sheet": null}}
    Q: What is shown in the infographic? → {{"source_types": ["images"], "year": null, "sheet": null}}
    Q: What does the MD&A ratio table show? → {{"source_types": ["images"], "year": null, "sheet": null}}
    Q: According to the MD&A what was the reason for decline? → {{"source_types": ["pdf"], "year": null, "sheet": null}}
    Q: What does the BRSR disclose? → {{"source_types": ["pdf"], "year": null, "sheet": null}}
    Q: What KAM did the auditor identify? → {{"source_types": ["pdf"], "year": null, "sheet": null}}

    Return ONLY a JSON object, no explanation, no markdown:
    {{"source_types": ["pdf"], "year": "2022", "sheet": null}}

    Question: {question}
    """

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        start_t = time.time()
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            duration = time.time() - start_t
            from app.core.token_tracker import record_token_usage
            record_token_usage(response)
            OPENAI_CALL_LATENCY.labels(model="gpt-4.1-mini", purpose="routing").observe(duration)
            OPENAI_CALL_COUNT.labels(model="gpt-4.1-mini", purpose="routing", status="success").inc()
        except Exception as api_err:
            duration = time.time() - start_t
            OPENAI_CALL_LATENCY.labels(model="gpt-4.1-mini", purpose="routing").observe(duration)
            OPENAI_CALL_COUNT.labels(model="gpt-4.1-mini", purpose="routing", status="error").inc()
            raise api_err
            
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        source_types = result.get("source_types", [])
        # Normalize — LLM sometimes returns full collection name
        source_types = [s.replace(f"{company_slug}_", "") for s in source_types]
        if not source_types:
            raise ValueError("empty source_types")
        routed_year = result.get("year") or extracted_year
        detected_sheet = result.get("sheet")
        collections = [f"{company_slug}_{source_type}" for source_type in source_types]

        logger.info(f"[Router] LLM → {source_types} | Year: {routed_year} | Sheet: {detected_sheet}")

        return RouteDecision(
            source_types=source_types,
            year=routed_year,
            agent_used="llm",
            collections_searched=collections,
            sheet=detected_sheet,
        )
    except Exception:
        logger.warning("[Router] LLM routing failed, falling back to keywords")
        return _keyword_route(question, company_slug, extracted_year)
