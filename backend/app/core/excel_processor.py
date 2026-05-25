from pathlib import Path

import pandas as pd
from loguru import logger
from config import settings

def _normalize_label(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()

def _find_row_index(df: pd.DataFrame, label: str) -> int | None:
    target = label.strip().lower()
    for idx, row in df.iterrows():
        first_cell = _normalize_label(row.iloc[0] if len(row) > 0 else "")
        if first_cell == target:
            return idx
    return None

def get_company_name(df: pd.DataFrame) -> str:
    company_row_idx = _find_row_index(df, "COMPANY NAME")
    if company_row_idx is None:
        return "Unknown Company"

    row = df.iloc[company_row_idx]
    for col_idx in range(1, len(row)):
        value = row.iloc[col_idx]
        if pd.notna(value):
            company_name = str(value).strip()
            if company_name:
                return company_name.title()

    return "Unknown Company"

def _parse_fiscal_years(header_row: pd.Series) -> list[str]:
    fiscal_years: list[str] = []
    for val in header_row.iloc[1:]:
        if pd.isna(val):
            fiscal_years.append("")
            continue
        try:
            if hasattr(val, "year"):
                dt = val
            else:
                dt = pd.to_datetime(val)
            year = dt.year + 1 if dt.month >= 4 else dt.year
            fiscal_years.append(f"FY{year}")
        except Exception:
            fiscal_years.append("")
    logger.info(f"Fiscal years parsed: {fiscal_years}")
    return fiscal_years

def _format_value(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return f"{float(value):.2f} Cr"
    value_str = str(value).strip()
    if not value_str:
        return None
    return value_str

def _collect_metrics(
    df: pd.DataFrame,
    start_label: str,
    end_label: str,
    metric_names: list[str]
) -> dict[str, dict[int, object]]:
    start_idx = _find_row_index(df, start_label)
    end_idx = len(df) if not end_label else _find_row_index(df, end_label)
    if start_idx is None:
        return {}

    if end_idx is None or end_idx <= start_idx:
        end_idx = len(df)

    metrics: dict[str, dict[int, object]] = {}
    label_to_metric = {m.lower(): m for m in metric_names}

    for idx in range(start_idx + 1, end_idx):
        row = df.iloc[idx]
        label = _normalize_label(row.iloc[0] if len(row) > 0 else "")
        if label in label_to_metric:
            metric = label_to_metric[label]
            values_by_col: dict[int, object] = {}
            for col_idx in range(1, len(row)):
                values_by_col[col_idx] = row.iloc[col_idx]
            metrics[metric] = values_by_col

    return metrics

def extract_excel(file_path: str) -> list[dict]:
    """
    Extracts structured financial metrics from the "Data Sheet" sheet.
    Returns list of dicts with content and metadata.
    """
    excel_path = file_path
    logger.info(f"Processing Excel: {excel_path}")

    df = pd.read_excel(excel_path, sheet_name="Data Sheet", header=None)

    report_date_idx = _find_row_index(df, "Report Date")
    if report_date_idx is None:
        logger.error("Report Date row not found in Data Sheet")
        return []

    fiscal_years = _parse_fiscal_years(df.iloc[report_date_idx])

    profit_loss_metrics = [
        "Sales",
        "Raw Material Cost",
        "Change in Inventory",
        "Power and Fuel",
        "Other Mfr. Exp",
        "Employee Cost",
        "Selling and admin",
        "Other Expenses",
        "Other Income",
        "Depreciation",
        "Interest",
        "Profit before tax",
        "Tax",
        "Net profit",
        "Dividend Amount",
    ]

    balance_sheet_metrics = [
        "Equity Share Capital",
        "Reserves",
        "Borrowings",
        "Other Liabilities",
        "Net Block",
        "Capital Work in Progress",
        "Investments",
        "Other Assets",
        "Receivables",
        "Inventory",
        "Cash & Bank",
    ]

    cash_flow_metrics = [
        "Cash from Operating Activity",
        "Cash from Investing Activity",
        "Cash from Financing Activity",
        "Net Cash Flow",
    ]

    profit_loss = _collect_metrics(df, "PROFIT & LOSS", "Quarters", profit_loss_metrics)
    balance_sheet = _collect_metrics(df, "BALANCE SHEET", "CASH FLOW:", balance_sheet_metrics)
    cash_flow = _collect_metrics(df, "CASH FLOW:", "", cash_flow_metrics)
    logger.info(f"Cash flow metrics found: {list(cash_flow.keys())}")

    chunks: list[dict] = []
    source_path = file_path
    filename = Path(file_path).name
    company_name = get_company_name(df)

    section_map = [
        ("Profit & Loss", "profit_loss", profit_loss),
        ("Balance Sheet", "balance_sheet", balance_sheet),
        ("Cash Flow", "cash_flow", cash_flow),
    ]

    for section_title, sheet_key, metrics in section_map:
        for col_offset, fy in enumerate(fiscal_years, start=1):
            if not fy:
                continue
            year_num = fy.replace("FY", "")
            lines = [f"{company_name} - {section_title} | {fy}"]

            def get_metric_value(name: str) -> str | None:
                if name not in metrics:
                    return None
                return _format_value(metrics[name].get(col_offset))

            for metric_name in metrics.keys():
                value = get_metric_value(metric_name)
                if value is None:
                    continue
                lines.append(f"{metric_name}: {value}")

            if section_title == "Profit & Loss":
                ebitda_components = [
                    "Raw Material Cost",
                    "Power and Fuel",
                    "Other Mfr. Exp",
                    "Employee Cost",
                    "Selling and admin",
                    "Other Expenses",
                ]

                sales_val = None
                sales = get_metric_value("Sales")
                if sales:
                    sales_val = float(sales.replace(" Cr", ""))

                if sales_val:
                    total_expenses = 0
                    for comp in ebitda_components:
                        val = get_metric_value(comp)
                        if val:
                            total_expenses += float(val.replace(" Cr", ""))
                    ebitda_value = sales_val - total_expenses
                    lines.append(f"EBITDA: {ebitda_value:.2f} Cr")

            if section_title == "Balance Sheet":
                equity = get_metric_value("Equity Share Capital")
                reserves = get_metric_value("Reserves")
                if equity and reserves:
                    try:
                        networth_value = (
                            float(equity.replace(" Cr", "")) +
                            float(reserves.replace(" Cr", ""))
                        )
                        lines.append(f"Networth: {networth_value:.2f} Cr")
                    except ValueError:
                        pass

            if len(lines) == 1:
                continue

            chunks.append({
                "content": "\n".join(lines),
                "metadata": {
                    "filename": filename,
                    "sheet": sheet_key,
                    "year": year_num,
                    "chunk_type": "table",
                    "source": source_path,
                    "collection": "ca_structured_financials",
                }
            })

    logger.success(f"Extracted {len(chunks)} structured chunks from Excel")
    return chunks
