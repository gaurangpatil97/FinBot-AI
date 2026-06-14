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
    """
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

    is_ebitda_margin = False
    if question:
        q_lower = question.lower()
        if any(phrase in q_lower for phrase in ["ebitda margin", "margin trend", "operating margin"]):
            is_ebitda_margin = True

    if is_ebitda_margin and not force_raw:
        margin_data = []
        for year in years:
            try:
                intent = HARDCODED_FORMULAS["ebitda margin"].copy()
                intent["years"] = [year]
                computed = compute_answer(intent, company_slug=company_slug)
                val = computed.get("answer") if computed else 0.0
            except Exception:
                val = 0.0
            margin_data.append(val if val is not None else 0.0)
            
        x_axis = [f"FY{y[-2:]}" if len(y) == 4 else y for y in years]
        title = f"EBITDA MARGIN {x_axis[0]}–{x_axis[-1]}"
        
        return ChartData(
            chart_type="bar",
            title=title,
            x_axis=x_axis,
            series=[ChartSeries(name="EBITDA Margin", data=margin_data)],
            y_axis_label="%"
        )

    # Determine chart type
    if len(metrics) == 1:
        chart_type = "line" if (chart_type_hint == "line") else "bar"
    elif len(metrics) == 2:
        chart_type = "combo"
    else:
        chart_type = chart_type_hint or "bar"

    series_list: List[ChartSeries] = []
    
    # We will search across all three sheets for each metric
    sheets = ["profit_loss", "balance_sheet", "cash_flow"]

    for metric in metrics:
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
            
            # Use 0.0 or None/0 if not found, we'll store 0.0 for missing values
            data_points.append(val if val is not None else 0.0)
            
        series_list.append(ChartSeries(name=metric, data=data_points))

    # X-axis labels: e.g. ["FY22", "FY23", ...]
    x_axis = [f"FY{y[-2:]}" if len(y) == 4 else y for y in years]

    # Create a descriptive title
    title = f"{', '.join(metrics)} over {x_axis[0]}–{x_axis[-1]}" if x_axis else f"{', '.join(metrics)}"
    
    is_comparison = False
    if question and len(metrics) == 2:
        q_lower = question.lower()
        if any(keyword in q_lower for keyword in [" vs ", "vs.", "compare", " and ", "over time"]):
            is_comparison = True

    if is_comparison and x_axis:
        m1 = metrics[0].upper().replace("SALES", "REVENUE")
        m2 = metrics[1].upper().replace("SALES", "REVENUE")
        title = f"{m1} vs {m2} {x_axis[0]}–{x_axis[-1]}"

    # Determine a suitable Y-axis label if applicable (default to Cr)
    y_axis_label = "Value (Cr)"

    secondary_y_axis = False
    if chart_type == "combo" and len(series_list) == 2:
        s1_max = max([abs(x) for x in series_list[0].data]) if series_list[0].data else 0
        s2_max = max([abs(x) for x in series_list[1].data]) if series_list[1].data else 0
        if s1_max > 0 and s2_max > 0:
            ratio = s1_max / s2_max
            if ratio > 10 or ratio < 0.1:
                secondary_y_axis = True

    raw_chart = ChartData(
        chart_type=chart_type,
        title=title,
        x_axis=x_axis,
        series=series_list,
        y_axis_label=y_axis_label,
        secondary_y_axis=secondary_y_axis
    )

    if not force_raw and question:
        q_lower = question.lower()
        keywords = ["growth rate", "year-on-year growth", "yoy growth", "rate of growth", "how fast", "grew"]
        if any(kw in q_lower for kw in keywords) and len(years) >= 2:
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
            
            metrics_upper = ", ".join(metrics).upper()
            if "SALES" in metrics_upper:
                metrics_upper = metrics_upper.replace("SALES", "REVENUE")
            new_title = f"{metrics_upper} GROWTH RATE {x_axis[0]}–{x_axis[-1]}"
            
            return ChartData(
                chart_type="bar",
                title=new_title,
                x_axis=new_x_axis,
                series=growth_series,
                y_axis_label="%"
            )

    return raw_chart

