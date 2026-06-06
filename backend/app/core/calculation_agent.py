import json
import re
import ast

import chromadb
import openai
from config import get_settings
from loguru import logger
from app.db.vector_store import get_persistent_client

settings = get_settings()

HARDCODED_FORMULAS = {
    "debt to equity": {
        "computation_type": "ratio",
        "formula": "metric1 / metric2",
        "metrics": [
            {"name": "Borrowings", "sheet": "balance_sheet"},
            {"name": "Networth", "sheet": "balance_sheet"}
        ],
        "multiply_by_100": False
    },
    "cash conversion": {
        "computation_type": "ratio",
        "formula": "metric1 / metric2",
        "metrics": [
            {"name": "Cash from Operating Activity", "sheet": "cash_flow"},
            {"name": "Net profit", "sheet": "profit_loss"}
        ],
        "multiply_by_100": False
    },
    "interest coverage": {
        "computation_type": "ratio",
        "formula": "metric1 / metric2",
        "metrics": [
            {"name": "EBITDA", "sheet": "profit_loss"},
            {"name": "Interest", "sheet": "profit_loss"}
        ],
        "multiply_by_100": False
    },
    "revenue growth": {
        "computation_type": "percentage",
        "formula": "((metric2 - metric1) / metric1) * 100",
        "metrics": [
            {"name": "Sales", "sheet": "profit_loss"}
        ],
        "multiply_by_100": False
    },
    "net profit margin": {
        "computation_type": "percentage",
        "formula": "(metric1 / metric2) * 100",
        "metrics": [
            {"name": "Net profit", "sheet": "profit_loss"},
            {"name": "Sales", "sheet": "profit_loss"}
        ],
        "multiply_by_100": False
    },
    "roe": {
        "computation_type": "percentage",
        "formula": "(metric1 / metric2) * 100",
        "metrics": [
            {"name": "Net profit", "sheet": "profit_loss"},
            {"name": "Networth", "sheet": "balance_sheet"}
        ],
        "multiply_by_100": False
    },
    "return on equity": {
        "computation_type": "percentage",
        "formula": "(metric1 / metric2) * 100",
        "metrics": [
            {"name": "Net profit", "sheet": "profit_loss"},
            {"name": "Networth", "sheet": "balance_sheet"}
        ],
        "multiply_by_100": False
    },
    "ebitda margin": {
        "computation_type": "percentage",
        "formula": "(metric1 / metric2) * 100",
        "metrics": [
            {"name": "EBITDA", "sheet": "profit_loss"},
            {"name": "Sales", "sheet": "profit_loss"}
        ],
        "multiply_by_100": False
    },
}

HARDCODED_FORMULA_ALIASES = {
    "debt to equity": ["debt to equity", "debt-to-equity", "dte"],
    "cash conversion": ["cash conversion", "cash conversion ratio", "cash conversion ratio ", "ccr"],
    "interest coverage": ["interest coverage", "interest coverage ratio", "icr"],
    "revenue growth": [
        "revenue growth",
        "revenue grew",
        "growth in revenue",
        "growth rate of revenue",
        "percentage revenue growth",
        "revenue increase"
    ],
    "net profit margin": ["net profit margin", "npm"],
    "roe": ["roe", "return on equity"],
    "return on equity": ["return on equity", "roe"],
    "ebitda margin": ["ebitda margin"],
}


def _normalize_year(year: str) -> str:
    return str(year).replace("FY", "").strip()


def _match_hardcoded_formula(question: str) -> dict | None:
    lowered = question.lower()
    for key, formula_template in HARDCODED_FORMULAS.items():
        aliases = HARDCODED_FORMULA_ALIASES.get(key, [key])
        if any(alias in lowered for alias in aliases):
            years = re.findall(r"20\d\d", question)
            if not years:
                years = re.findall(r"FY(\d\d)", question)
                years = [f"20{year}" for year in years]

            result = formula_template.copy()
            result["years"] = years if years else []
            logger.info(f"[CalcAgent] Using hardcoded formula for: {key}")
            return result
    return None


def is_computation_question(question: str) -> dict:
    prompt = f'''You are a financial query classifier. Classify this question into one of these types:
- lookup: asking for a specific stored value (e.g. what was revenue in FY22)
- ratio: asking for a ratio or coverage metric (e.g. debt to equity, interest coverage)
- margin: asking for a margin percentage (e.g. EBITDA margin, net profit margin)
- growth: asking for growth rate between two periods
- derived: any other calculation requiring arithmetic

Return ONLY JSON: {{"type": "lookup", "needs_calculation": false}} or {{"type": "ratio", "needs_calculation": true}}

Rule: lookup returns needs_calculation=false. All others return needs_calculation=true.

Question: {question}'''

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        query_type = result.get("type", "lookup")
        needs_calculation = result.get("needs_calculation")
        if isinstance(query_type, str) and isinstance(needs_calculation, bool):
            logger.info(
                f"[CalcAgent] LLM computation check for: {question[:50]} → {query_type} / {needs_calculation}"
            )
            return {"type": query_type, "needs_calculation": needs_calculation}
    except Exception as exc:
        logger.warning(f"[CalcAgent] LLM computation detection failed, defaulting to False: {exc}")

    return {"type": "lookup", "needs_calculation": False}


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
    "years": [] if no year is mentioned, or ["2023", "2025"] for trend,
  "multiply_by_100": true or false
}}
"""

    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as exc:
        logger.error(f"Failed to parse computation intent: {exc}")
        return None


def fetch_metric(metric_name: str, sheet: str, year: str, company_slug: str | None = None) -> float | None:
    try:
        year = str(year).strip()
        year = re.sub(r"^FY\s*", "", year, flags=re.IGNORECASE).strip()
        if len(year) == 2 and year.isdigit():
            year = f"20{year}"
        # Always scope to company — reject calls without slug.
        if not company_slug:
            logger.error("[CalcAgent] company_slug is required — no global Excel collection")
            return None

        collection_name = f"{company_slug}_excel"
        company_client = get_persistent_client(
            str(settings.BASE_DIR / "chroma_store" / company_slug / "excel")
        )
        collection = company_client.get_collection(collection_name)
        results = collection.get(
            where={"$and": [{"year": year}, {"sheet": sheet}]},
            include=["documents", "metadatas"]
        )

        documents = results.get("documents", []) or []

        def find_value(name_to_search: str) -> float | None:
            for document in documents:
                for line in str(document).splitlines():
                    stripped = line.strip()
                    if not stripped.lower().startswith(name_to_search.lower()):
                        continue
                    # Unit-agnostic — works beyond Indian Cr format.
                    match = re.search(r"([-+]?\d*\.?\d+)\s*(?:Cr|cr|CR|M|B|L|lakh|mn|bn)?\b", stripped)
                    if match:
                        return float(match.group(1))
                    number_match = re.search(r"([-+]?\d*\.?\d+)", stripped)
                    if number_match:
                        return float(number_match.group(1))
            return None

        def find_partial_value(name_to_search: str) -> float | None:
            for document in documents:
                for line in str(document).splitlines():
                    stripped = line.strip()
                    if name_to_search.lower() not in stripped.lower():
                        continue
                    number_match = re.search(r"([-+]?\d*\.?\d+)", stripped)
                    if not number_match:
                        continue
                    prefix = stripped[:number_match.start()]
                    prefix_without_metric = re.sub(re.escape(name_to_search), "", prefix, flags=re.IGNORECASE)
                    if any(ch.isalpha() for ch in prefix_without_metric):
                        continue
                    # Unit-agnostic — works beyond Indian Cr format.
                    match = re.search(r"([-+]?\d*\.?\d+)\s*(?:Cr|cr|CR|M|B|L|lakh|mn|bn)?\b", stripped)
                    if match:
                        value = float(match.group(1))
                        logger.warning(f"[CalcAgent] Using partial match for '{name_to_search}' — verify result: {value}")
                        return value
            return None

        val = find_value(metric_name)
        if val is not None:
            return val

        # Try singular/plural variant by stripping or adding a trailing s
        if metric_name.endswith("s") or metric_name.endswith("S"):
            variant = metric_name[:-1]
        else:
            variant = metric_name + "s"

        logger.info(f"[CalcAgent] Exact match failed for '{metric_name}', retrying with variant '{variant}'")
        val_variant = find_value(variant)
        if val_variant is not None:
            return val_variant

        # Try partial contains match
        logger.info(f"[CalcAgent] Variant match failed, retrying with partial contains match for '{metric_name}'")
        return find_partial_value(metric_name)
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


def compute_answer(intent: dict, company_slug: str | None = None) -> dict | None:
    try:
        metrics = intent.get("metrics", [])
        years = [_normalize_year(year) for year in intent.get("years", [])]
        formula = intent.get("formula", "")
        multiply_by_100 = bool(intent.get("multiply_by_100", False))
        computation_type = intent.get("computation_type", "derived")

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
        metrics_used: list[dict[str, str | float]] = []

        for index, (metric, year) in enumerate(metric_year_pairs, start=1):
            metric_name = metric.get("name")
            sheet = metric.get("sheet")
            value = fetch_metric(metric_name, sheet, year, company_slug=company_slug)
            logger.info(f"[CalcAgent] Fetched {metric_name} FY{year}: {value}")
            if value is None:
                return None

            placeholder = f"metric{index}"
            variable_name = f"{metric_name.replace(' ', '_').replace('&', 'and')}_{year}"
            variables[placeholder] = value
            values_used[variable_name] = value
            metrics_used.append({
                "name": metric_name,
                "sheet": sheet,
                "year": year,
                "value": value,
            })

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

        # Replace placeholders like metric1, metric2... in the reported formula
        display_formula = formula
        for index, (metric, year) in enumerate(metric_year_pairs, start=1):
            metric_name = metric.get("name", "")
            display_formula = display_formula.replace(f"metric{index}", metric_name)

        return {
            "answer": result,
            "formula_used": display_formula,
            "values_used": values_used,
            "metrics_used": metrics_used,
            "computation_type": computation_type,
            "year": year_value,
        }
    except Exception as exc:
        logger.error(f"Failed to compute answer: {exc}")
        return None


def try_calculation(question: str, company_slug: str | None = None) -> dict | None:
    trace: list[str] = []
    trace.append("Detected: computation question")
    logger.info(f"[CalcAgent] Checking question: {question}")

    intent = _match_hardcoded_formula(question)
    if intent is None:
        classification = is_computation_question(question)
        logger.info(f"[CalcAgent] Classification: {classification}")
        if not classification.get("needs_calculation"):
            logger.warning("[CalcAgent] Falling back to RAG at step: is_computation_question")
            return None

        intent = parse_computation_intent(question)
        logger.info(f"[CalcAgent] Parsed intent: {intent}")
        if intent is None:
            logger.warning("[CalcAgent] Falling back to RAG at step: parse_computation_intent")
            return None

    if intent.get("computation_type") == 'trend' and len(intent.get("years", [])) >= 2:
        logger.warning('[CalcAgent] Multi-year trend detected, falling back to RAG + clarifier')
        return None

    metrics = intent.get("metrics", [])
    years = [_normalize_year(year) for year in intent.get("years", [])]
    if len(years) >= 2:
        metric_name = metrics[0].get("name") if metrics else "unknown"
        results: list[dict[str, object]] = []
        trace.append(f"Multi-year metric: {metric_name}")

        for year in years:
            year_intent = dict(intent)
            year_intent["years"] = [year]

            computed = compute_answer(year_intent, company_slug=company_slug)
            logger.info(f"[CalcAgent] Multi-year computed result for FY{year}: {computed}")
            if computed is None:
                return None

            results.append({
                "year": year,
                "answer": computed.get("answer"),
                "formula_used": computed.get("formula_used"),
                "values_used": computed.get("values_used"),
            })

        trace.append("Multi-year lookup completed")
        return {
            "multi_year": True,
            "metric_name": metric_name,
            "results": results,
            "year": years[-1] if years else "computed",
            "trace": "\n".join(trace),
        }

    trace.append(f"Intent: {intent.get('computation_type')}")
    trace.append(f"Formula: {intent.get('formula')}")

    computed = compute_answer(intent, company_slug=company_slug)
    logger.info(f"[CalcAgent] Computed result: {computed}")
    if computed is None:
        logger.warning("[CalcAgent] Falling back to RAG at step: compute_answer")
        return None

    for metric_name, metric_value in computed.get("values_used", {}).items():
        trace.append(f"Fetched {metric_name}: {metric_value}")
    trace.append(f"Result: {computed.get('answer')}")

    computed["trace"] = "\n".join(trace)

    return computed
