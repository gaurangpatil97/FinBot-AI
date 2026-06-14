from __future__ import annotations

from typing import List, Optional
from loguru import logger
from app.models.schemas import ChartData, ChartSeries
from app.core.calculation_agent import fetch_metric, HARDCODED_FORMULAS, compute_answer
from app.db.vector_store import get_persistent_client
from config import settings


def get_available_years(company_slug: str) -> List[str]:
    """Helper to retrieve all unique years present in the company's Excel database."""
    try:
        path = str(settings.BASE_DIR / "chroma_store" / company_slug / "excel")
        company_client = get_persistent_client(path)
        collection = company_client.get_collection(f"{company_slug}_excel")
        results = collection.get(include=["metadatas"])
        years = set()
        for meta in results.get("metadatas", []) or []:
            year = meta.get("year")
            if year and year != "unknown":
                # Normalize year to 4-digit format (e.g. "2024")
                y_str = str(year).strip()
                years.add(y_str)
        return sorted(list(years))
    except Exception as e:
        logger.warning(f"[ChartBuilder] Failed to get available years for {company_slug}: {e}")
        # Default fallback years
        return ["2022", "2023", "2024", "2025"]


def plan_chart(question: str) -> Optional[dict]:
    """Calls OpenAI to generate a structured chart plan from the user's natural language question."""
    # Get available ratios and metrics dynamically from the calc_agent registry
    available_ratios = list(HARDCODED_FORMULAS.keys())
    
    available_metrics = set()
    for formula in HARDCODED_FORMULAS.values():
        for metric_info in formula.get("metrics", []):
            available_metrics.add(metric_info["name"])
    
    # Ensure standard names are present
    available_metrics.update(["Sales", "EBITDA", "Net profit", "Borrowings", "Networth", "Interest", "Depreciation"])
    available_metrics_list = sorted(list(available_metrics))
    
    prompt = f"""You are a financial chart planning agent.
Analyze the user's query and generate a structured chart plan.

Available standard metrics to plot:
{json.dumps(available_metrics_list)}

Available ratio formulas:
{json.dumps(available_ratios)}

Strict Rules:
1. Map the query to one of these four chart kinds:
   - "single_metric": plotting a single raw metric over time.
   - "growth_rate": plotting the year-over-year % growth rate of a single metric over time.
   - "ratio": plotting a computed ratio/margin over time.
   - "comparison": comparing two raw metrics over time.
2. In the "metrics" array, provide the exact metric names from the available standard metrics list above. 
   - For "single_metric" and "growth_rate", provide exactly 1 metric.
   - For "comparison", provide exactly 2 metrics to compare.
   - For "ratio", leave "metrics" empty or null.
3. In "ratio", if the chart_kind is "ratio", provide the exact ratio name from the available ratio formulas list above (e.g., "ebitda margin", "debt to equity"). Otherwise, set "ratio" to null.
4. Extract the year range from the query. If a start year or end year is mentioned (like FY22 or 2025), normalize it to "FY22" or "FY25" style. If no years are mentioned, set them to null.

You MUST return ONLY a JSON object, with no markdown, no backticks, and no extra text:
{{
  "chart_kind": "single_metric" | "growth_rate" | "ratio" | "comparison",
  "metrics": ["EBITDA"],
  "ratio": null,
  "year_start": "FY22" or null,
  "year_end": "FY25" or null
}}

User query: {question}"""

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        # Remove backticks/markdown formatting if present
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```json"):
                content = "\n".join(lines[1:-1])
            elif lines[0].startswith("```"):
                content = "\n".join(lines[1:-1])
        plan = json.loads(content.strip())
        logger.info(f"[ChartPlanner] Structured plan: {plan}")
        return plan
    except Exception as e:
        logger.error(f"[ChartPlanner] Planning failed: {e}")
        return None


def build_chart_data(
    company_slug: str,
    metrics: List[str],
    years: Optional[List[str]] = None,
    chart_type_hint: Optional[str] = None,
    question: Optional[str] = None,
    force_raw: bool = False
) -> ChartData:
    """
    Fetches the metric values for the specified company, metrics, and years,
    and returns a renderer-agnostic ChartData spec.
    Uses LLM structured planner if a natural language question is provided.
    """
    # 1. Resolve initial years range if not provided
    if not years:
        years = get_available_years(company_slug)
    else:
        # Normalize requested years
        normalized_years = []
        for y in years:
            y_clean = str(y).replace("FY", "").strip()
            if len(y_clean) == 2 and y_clean.isdigit():
                y_clean = f"20{y_clean}"
            normalized_years.append(y_clean)
        
        # Sort and remove duplicates
        years = sorted(list(set(normalized_years)))
        
        # Range expansion: if exactly 2 years are passed (start and end), expand inclusive
        if len(years) == 2:
            try:
                start_y = int(years[0])
                end_y = int(years[1])
                if start_y < end_y and (end_y - start_y) <= 10:
                    years = [str(y) for y in range(start_y, end_y + 1)]
            except ValueError:
                pass

    # 2. Get available metrics and ratios dynamically
    available_ratios = list(HARDCODED_FORMULAS.keys())
    available_metrics = set()
    for formula in HARDCODED_FORMULAS.values():
        for metric_info in formula.get("metrics", []):
            available_metrics.add(metric_info["name"])
    available_metrics.update(["Sales", "EBITDA", "Net profit", "Borrowings", "Networth", "Interest", "Depreciation"])
    available_metrics_list = sorted(list(available_metrics))

    # 3. Call planner if natural language question is provided
    chart_kind = "single_metric"
    plan_metrics = metrics or ["Sales"]
    plan_ratio = None

    if question:
        plan = plan_chart(question)
        if plan:
            chart_kind = plan.get("chart_kind", "single_metric")
            plan_metrics = plan.get("metrics", [])
            plan_ratio = plan.get("ratio")
            
            # Extract planned years if available in the LLM plan
            if plan.get("year_start") and plan.get("year_end"):
                y_start = str(plan["year_start"]).replace("FY", "").replace(" ", "").strip()
                y_end = str(plan["year_end"]).replace("FY", "").replace(" ", "").strip()
                if len(y_start) == 2 and y_start.isdigit():
                    y_start = f"20{y_start}"
                if len(y_end) == 2 and y_end.isdigit():
                    y_end = f"20{y_end}"
                try:
                    start_y = int(y_start)
                    end_y = int(y_end)
                    if start_y < end_y and (end_y - start_y) <= 10:
                        years = [str(y) for y in range(start_y, end_y + 1)]
                except ValueError:
                    pass

    # 4. Safely validate and fallback planned inputs
    if chart_kind not in ["single_metric", "growth_rate", "ratio", "comparison"]:
        chart_kind = "single_metric"

    if chart_kind == "ratio":
        if plan_ratio not in available_ratios:
            # Plan invalid ratio: fallback gracefully to single_metric
            chart_kind = "single_metric"
            plan_metrics = ["Sales"]
            logger.warning(f"[ChartBuilder] Invalid planned ratio: {plan_ratio}. Falling back to single_metric.")
    else:
        # Validate metrics
        validated_metrics = []
        for m in plan_metrics:
            matched = None
            for avail in available_metrics_list:
                if avail.lower() == m.lower() or avail.lower().replace(" ", "") == m.lower().replace(" ", ""):
                    matched = avail
                    break
            if matched:
                validated_metrics.append(matched)
        
        if not validated_metrics:
            validated_metrics = ["Sales"]
            chart_kind = "single_metric"
            logger.warning(f"[ChartBuilder] No valid planned metrics. Falling back to single_metric on Sales.")
        elif chart_kind == "comparison" and len(validated_metrics) < 2:
            chart_kind = "single_metric"
            logger.warning(f"[ChartBuilder] Not enough metrics for comparison. Falling back to single_metric.")
            
        plan_metrics = validated_metrics[:2] if chart_kind == "comparison" else validated_metrics[:1]

    # 5. Execute Plan
    x_axis = [f"FY{y[-2:]}" if len(y) == 4 else y for y in years]

    if chart_kind == "ratio":
        # Compute ratio/margin trend per year using calc_agent formula
        margin_data = []
        for year in years:
            try:
                intent = HARDCODED_FORMULAS[plan_ratio].copy()
                intent["years"] = [year]
                computed = compute_answer(intent, company_slug=company_slug)
                val = computed.get("answer") if computed else 0.0
            except Exception:
                val = 0.0
            margin_data.append(val if val is not None else 0.0)
            
        ratio_display_name = plan_ratio.upper()
        if "EBITDA MARGIN" in ratio_display_name:
            ratio_display_name = "EBITDA MARGIN"
        title = f"{ratio_display_name} {x_axis[0]}–{x_axis[-1]}"
        
        return ChartData(
            chart_type="bar",
            title=title,
            x_axis=x_axis,
            series=[ChartSeries(name=plan_ratio.title(), data=margin_data)],
            y_axis_label="%"
        )

    # For standard, growth, and comparison chart kinds, fetch underlying metrics first
    sheets = ["profit_loss", "balance_sheet", "cash_flow"]
    series_list = []
    for metric in plan_metrics:
        data_points = []
        for year in years:
            val = None
            for sheet in sheets:
                try:
                    val = fetch_metric(metric, sheet, year, company_slug)
                    if val is not None:
                        break
                except Exception:
                    continue
            data_points.append(val if val is not None else 0.0)
        series_list.append(ChartSeries(name=metric, data=data_points))

    # growth_rate executor logic (YoY math on raw series)
    if chart_kind == "growth_rate" and not force_raw:
        if len(years) >= 2:
            growth_series = []
            for series in series_list:
                growth_data = []
                for i in range(len(series.data) - 1):
                    prev = series.data[i]
                    curr = series.data[i+1]
                    if prev != 0.0:
                        rate = ((curr - prev) / prev) * 100
                    else:
                        rate = 0.0
                    growth_data.append(round(rate, 2))
                growth_series.append(ChartSeries(name=series.name, data=growth_data))
                
            new_x_axis = [f"{x_axis[i]}→{x_axis[i+1]}" for i in range(len(x_axis) - 1)]
            metrics_upper = ", ".join(plan_metrics).upper().replace("SALES", "REVENUE")
            new_title = f"{metrics_upper} GROWTH RATE {x_axis[0]}–{x_axis[-1]}"
            
            return ChartData(
                chart_type="bar",
                title=new_title,
                x_axis=new_x_axis,
                series=growth_series,
                y_axis_label="%"
            )

    # single_metric / comparison executor logic
    if chart_kind == "comparison":
        chart_type = "combo"
        m1 = plan_metrics[0].upper().replace("SALES", "REVENUE")
        m2 = plan_metrics[1].upper().replace("SALES", "REVENUE")
        title = f"{m1} vs {m2} {x_axis[0]}–{x_axis[-1]}"
    else:
        chart_type = chart_type_hint or "bar"
        title = f"{', '.join(plan_metrics)} over {x_axis[0]}–{x_axis[-1]}"

    # Determine secondary Y-axis flag for combo charts
    secondary_y_axis = False
    if chart_type == "combo" and len(series_list) == 2:
        s1_max = max([abs(x) for x in series_list[0].data]) if series_list[0].data else 0
        s2_max = max([abs(x) for x in series_list[1].data]) if series_list[1].data else 0
        if s1_max > 0 and s2_max > 0:
            ratio = s1_max / s2_max
            if ratio > 10 or ratio < 0.1:
                secondary_y_axis = True

    return ChartData(
        chart_type=chart_type,
        title=title,
        x_axis=x_axis,
        series=series_list,
        y_axis_label="Value (Cr)",
        secondary_y_axis=secondary_y_axis
    )

