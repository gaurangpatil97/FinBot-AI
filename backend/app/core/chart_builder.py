from __future__ import annotations

from typing import List, Optional
from loguru import logger
from app.models.schemas import ChartData, ChartSeries
from app.core.calculation_agent import fetch_metric
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
    chart_type_hint: Optional[str] = None
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
    
    # Determine a suitable Y-axis label if applicable (default to Cr)
    y_axis_label = "Value (Cr)"

    return ChartData(
        chart_type=chart_type,
        title=title,
        x_axis=x_axis,
        series=series_list,
        y_axis_label=y_axis_label
    )
