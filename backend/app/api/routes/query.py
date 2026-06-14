from __future__ import annotations

import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
import openai
from loguru import logger

from app.core.rag import answer_query
from app.models.schemas import QueryRequest, QueryResponse, ChartRequest, ChartData, Citation
from app.core.chart_builder import build_chart_data
from app.db import sessions_db
from config import settings

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    start_time = time.time()
    response = answer_query(request)
    latency = time.time() - start_time
    
    if request.session_id:
        # Save user message
        sessions_db.add_message(
            session_id=request.session_id,
            role="user",
            content=request.question,
            citations=[],
            routing_debug={},
            latency=0.0
        )
        
        # Save assistant message
        sessions_db.add_message(
            session_id=request.session_id,
            role="assistant",
            content=response.answer,
            citations=response.citations,
            routing_debug=response.routing_debug,
            latency=latency,
            chunks=response.chunks
        )
        
    return response


@router.post("/chart")
def generate_chart(request: ChartRequest):
    try:
        chart_data = build_chart_data(
            company_slug=request.company_slug,
            metrics=request.metrics,
            years=request.years,
            chart_type_hint=request.chart_type_hint,
            question=request.question
        )
        return {"chart_data": chart_data}
    except Exception as e:
        logger.error(f"[Chart API] Failed to generate chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_median(lst: List[float]) -> float:
    sorted_lst = sorted(lst)
    n = len(sorted_lst)
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return sorted_lst[n // 2]
    else:
        return (sorted_lst[n // 2 - 1] + sorted_lst[n // 2]) / 2.0


@router.post("/analyze", response_model=QueryResponse)
def analyze_trend(request: ChartRequest) -> QueryResponse:
    start_time = time.time()
    try:
        # 1. Fetch data & build chart spec using helper
        chart_data = build_chart_data(
            company_slug=request.company_slug,
            metrics=request.metrics,
            years=request.years,
            chart_type_hint=request.chart_type_hint,
            question=request.question,
            force_raw=True
        )
        
        # 2. Compute trend math deterministically in Python
        years = chart_data.x_axis
        
        analysis_details = []
        
        for series in chart_data.series:
            metric_name = series.name
            vals = series.data
            
            yoy_rates = []
            for i in range(len(vals) - 1):
                prev = vals[i]
                curr = vals[i+1]
                if prev != 0.0:
                    rate = ((curr - prev) / prev) * 100
                else:
                    rate = 0.0
                yoy_rates.append(round(rate, 2))
                
            # CAGR
            cagr = None
            if len(vals) >= 2:
                start_val = vals[0]
                end_val = vals[-1]
                n_periods = len(vals) - 1
                if start_val > 0.0 and end_val > 0.0:
                    try:
                        cagr = round(((end_val / start_val) ** (1.0 / n_periods) - 1.0) * 100.0, 2)
                    except Exception:
                        pass
            
            # Direction
            if cagr is not None:
                if cagr > 1.0:
                    direction = "improving"
                elif cagr < -1.0:
                    direction = "declining"
                else:
                    direction = "stable"
            else:
                direction = "stable"
                
            # Outliers (YoY rate > 1.5x median absolute YoY rate)
            abs_yoy = [abs(rate) for rate in yoy_rates]
            outliers = []
            if len(abs_yoy) >= 2:
                med_abs = get_median(abs_yoy)
                threshold = 1.5 * med_abs
                for i, rate in enumerate(yoy_rates):
                    if abs(rate) > threshold:
                        outliers.append({
                            "from_year": years[i],
                            "to_year": years[i+1],
                            "rate": rate,
                            "threshold": round(threshold, 2)
                        })
            
            analysis_details.append({
                "metric": metric_name,
                "values": vals,
                "yoy_rates": yoy_rates,
                "cagr": cagr,
                "direction": direction,
                "outliers": outliers
            })

        # 3. Build Prompt for LLM with pre-computed numbers
        precomputed_str = ""
        for detail in analysis_details:
            precomputed_str += f"\nMetric: {detail['metric']}\n"
            precomputed_str += f"- Values across {', '.join(years)}: {detail['values']}\n"
            precomputed_str += f"- YoY Growth Rates: {detail['yoy_rates']}\n"
            precomputed_str += f"- CAGR: {detail['cagr']}% (if computed)\n"
            precomputed_str += f"- Trend Direction: {detail['direction']}\n"
            if detail['outliers']:
                precomputed_str += f"- Outliers: {detail['outliers']} (defined as YoY rate exceeding 1.5x median absolute YoY rate)\n"
            else:
                precomputed_str += "- Outliers: None found\n"
                
        prompt = f"""You are a senior financial analyst helping a Chartered Accountant.
Below are the pre-computed financial numbers and trend metrics for {request.company_slug}:

{precomputed_str}

Write a natural-language analysis explaining these values.

Strict Rules:
1. Do NOT compute any new values. Use the pre-computed YoY rates, CAGR, and values verbatim.
2. The YoY growth rates are a list of consecutive year-over-year changes, whereas the CAGR is the single compound annual growth rate over the entire period. Do NOT equate them, and do not use the overall period growth rate as YoY or CAGR.
3. You MUST structure your response using the following layout and markdown ## headings (do NOT use bold-text-as-heading like **Summary:**):

## Summary
Provide a 1-2 sentence key conclusion and overall trend direction.

## Details
Provide a concise bulleted list narrating the YoY changes and CAGR.
If there are any outliers, explain them here, stating the exact rate and the 1.5x threshold rule.

## Sources
List the sources cleanly, e.g.:
{request.company_slug}_excel · profit_loss · {years[0]}–{years[-1]}

Do NOT output empty sections or "Not applicable" filler. If a section is not applicable, omit it entirely.
"""

        # 4. Make LLM call
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        answer = response.choices[0].message.content.strip()
        
        # Build citations
        citations = []
        for metric in request.metrics:
            citations.append(Citation(
                filename=f"{request.company_slug}_excel",
                page="calculation",
                collection=f"{request.company_slug}_excel"
            ))

        latency = time.time() - start_time
        
        # Build the final chart_data to return, applying growth rate formatting if requested
        final_chart_data = build_chart_data(
            company_slug=request.company_slug,
            metrics=request.metrics,
            years=request.years,
            chart_type_hint=request.chart_type_hint,
            question=request.question,
            force_raw=False
        )

        return QueryResponse(
            answer=answer,
            citations=citations,
            collections_searched=[f"{request.company_slug}_excel"],
            agent_used="trend_analysis_agent",
            agent_trace="Computed trend in Python + LLM narrative",
            chunks=[],
            routing_debug={
                "source_types": ["calculation"],
                "year": years[-1] if years else "",
                "method": "trend_analysis_agent"
            },
            chart_data=final_chart_data
        )
        
    except Exception as e:
        logger.error(f"[Analyze API] Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
