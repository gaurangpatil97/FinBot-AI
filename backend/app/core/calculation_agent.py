import json
import re
import ast

import chromadb
import ollama
from config import get_settings
from logger import logger

settings = get_settings()

chroma_client = chromadb.PersistentClient(
    path=settings.EXCEL_CHROMA_DIR,
    settings=chromadb.config.Settings(anonymized_telemetry=False)
)


def _normalize_year(year: str) -> str:
    return str(year).replace("FY", "").strip()


def is_computation_question(question: str) -> bool:
    lowered = question.lower()
    l2_keywords = [
        "margin", "ratio", "percentage", "coverage",
        "ebitda", "return on", "as a percentage",
    ]
    l3_keywords = [
        "debt to equity", "debt-to-equity", "roe",
        "cash conversion", "interest coverage",
    ]
    l4_keywords = [
        "grew by", "changed from", "difference between",
        "how much did", "growth from", "change from",
    ]

    logger.info(f"[CalcAgent] Keywords check for: {question[:50]}")

    result = any(keyword in lowered for keyword in l2_keywords)
    if not result:
        result = any(keyword in lowered for keyword in l3_keywords)

    years_mentioned = re.findall(r"FY20\d\d", question)
    if not result:
        result = len(years_mentioned) >= 2 and any(keyword in lowered for keyword in l4_keywords)

    logger.info(f"[CalcAgent] Result: {result}")

    return result


def parse_computation_intent(question: str) -> dict | None:
    prompt = f"""
You are a financial calculation agent.
Analyze this question and return ONLY a JSON object,
no explanation, no markdown, no backticks.

Question: {question}

Return this exact JSON structure:
{{
  "computation_type": "ratio" | "percentage" | "trend" | "derived",
  "formula": "metric1 / metric2" or "metric1 - metric2" or "(metric1 / metric2) * 100",
  "metrics": [
    {{"name": "exact metric name as in data", "sheet": "profit_loss" | "balance_sheet" | "cash_flow"}}
  ],
  "years": ["2025"] or ["2023", "2025"] for trend,
  "multiply_by_100": true or false
}}

Known metric names:
- profit_loss sheet: Sales, Net profit, Depreciation, Interest,
  Profit before tax, Tax, EBITDA, Dividend Amount, Raw Material Cost,
  Employee Cost
- balance_sheet sheet: Borrowings, Reserves, Equity Share Capital,
  Networth, Net Block, Other Liabilities, Receivables, Inventory,
  Cash & Bank
- cash_flow sheet: Cash from Operating Activity,
  Cash from Investing Activity, Cash from Financing Activity,
  Net Cash Flow

Common formulas:
- Debt to Equity = Borrowings / Networth
- Interest Coverage = EBITDA / Interest
- ROE = (Net profit / Networth) * 100
- Net Profit Margin = (Net profit / Sales) * 100
- Cash Conversion = Cash from Operating Activity / Net profit
- Interest % of Sales = (Interest / Sales) * 100
- EBITDA = Profit before tax + Depreciation + Interest
"""

    try:
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response["message"]["content"].strip()
        return json.loads(content)
    except Exception as exc:
        logger.error(f"Failed to parse computation intent: {exc}")
        return None


def fetch_metric(metric_name: str, sheet: str, year: str) -> float | None:
    try:
        year = _normalize_year(year)
        collection = chroma_client.get_collection(settings.EXCEL_COLLECTION_NAME)
        results = collection.get(
            where={"$and": [{"year": year}, {"sheet": sheet}]},
            include=["documents", "metadatas"]
        )

        documents = results.get("documents", []) or []
        for document in documents:
            for line in str(document).splitlines():
                stripped = line.strip()
                if not stripped.lower().startswith(metric_name.lower()):
                    continue
                match = re.search(r"([-+]?\d*\.?\d+)\s*Cr", stripped)
                if match:
                    return float(match.group(1))
                number_match = re.search(r"([-+]?\d*\.?\d+)", stripped)
                if number_match:
                    return float(number_match.group(1))
        return None
    except Exception as exc:
        logger.error(f"Failed to fetch metric {metric_name} for {sheet} {year}: {exc}")
        return None


def _safe_eval_expression(expression: str, variables: dict[str, float]) -> float | None:
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.Constant,
        ast.Name,
        ast.Load,
        ast.Mod,
        ast.FloorDiv,
        ast.Call,
    )

    allowed_functions = {"abs": abs, "round": round}

    try:
        tree = ast.parse(expression, mode="eval")
        for node in ast.walk(tree):
            if not isinstance(node, allowed_nodes):
                return None
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in allowed_functions:
                    return None
        compiled = compile(tree, "<calculation_agent>", "eval")
        return float(eval(compiled, {"__builtins__": {}}, {**allowed_functions, **variables}))
    except Exception:
        return None


def compute_answer(intent: dict) -> dict | None:
    try:
        metrics = intent.get("metrics", [])
        years = [_normalize_year(year) for year in intent.get("years", [])]
        formula = intent.get("formula", "")
        multiply_by_100 = bool(intent.get("multiply_by_100", False))

        metric_year_pairs: list[tuple[dict, str]] = []
        if len(metrics) == 1 and len(years) >= 2:
            metric_year_pairs = [(metrics[0], year) for year in years[:2]]
        elif len(years) == 1:
            metric_year_pairs = [(metric, years[0]) for metric in metrics]
        elif len(metrics) == len(years):
            metric_year_pairs = list(zip(metrics, years))
        else:
            for index, metric in enumerate(metrics):
                year = years[min(index, len(years) - 1)] if years else ""
                metric_year_pairs.append((metric, year))

        variables: dict[str, float] = {}
        values_used: dict[str, float] = {}

        for index, (metric, year) in enumerate(metric_year_pairs, start=1):
            metric_name = metric.get("name")
            sheet = metric.get("sheet")
            value = fetch_metric(metric_name, sheet, year)
            logger.info(f"[CalcAgent] Fetched {metric_name} FY{year}: {value}")
            if value is None:
                return None

            placeholder = f"metric{index}"
            variable_name = f"{metric_name.replace(' ', '_').replace('&', 'and')}_{year}"
            variables[placeholder] = value
            values_used[variable_name] = value

        evaluated_formula = formula
        for index, (metric, year) in enumerate(metric_year_pairs, start=1):
            metric_name = metric.get("name", "")
            # Replace the metric name in the formula with the placeholder
            evaluated_formula = evaluated_formula.replace(
                metric_name, f"metric{index}"
            )

        result = _safe_eval_expression(evaluated_formula, variables)
        if result is None:
            return None

        if multiply_by_100 and not re.search(r"\b100\b", formula):
            result *= 100

        result = round(result, 2)
        year_value = years[-1] if years else "computed"

        return {
            "answer": result,
            "formula_used": formula,
            "values_used": values_used,
            "year": year_value,
        }
    except Exception as exc:
        logger.error(f"Failed to compute answer: {exc}")
        return None


def try_calculation(question: str) -> dict | None:
    trace: list[str] = []
    trace.append("Detected: computation question")
    logger.info(f"[CalcAgent] Checking question: {question}")

    is_comp = is_computation_question(question)
    logger.info(f"[CalcAgent] Is computation question: {is_comp}")
    if not is_comp:
        logger.warning("[CalcAgent] Falling back to RAG at step: is_computation_question")
        return None

    intent = parse_computation_intent(question)
    logger.info(f"[CalcAgent] Parsed intent: {intent}")
    if intent is None:
        logger.warning("[CalcAgent] Falling back to RAG at step: parse_computation_intent")
        return None

    trace.append(f"Intent: {intent.get('computation_type')}")
    trace.append(f"Formula: {intent.get('formula')}")

    computed = compute_answer(intent)
    logger.info(f"[CalcAgent] Computed result: {computed}")
    if computed is None:
        logger.warning("[CalcAgent] Falling back to RAG at step: compute_answer")
        return None

    for metric_name, metric_value in computed.get("values_used", {}).items():
        trace.append(f"Fetched {metric_name}: {metric_value}")
    trace.append(f"Result: {computed.get('answer')}")

    computed["trace"] = "\n".join(trace)

    return computed