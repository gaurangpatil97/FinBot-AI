"""
FinBot Evaluation Script — run_eval_mini.py
Fires 15 stratified evaluation questions at the FinBot API and saves raw results.
"""

import json
import time
import requests
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 stdout for Windows
sys.stdout.reconfigure(encoding='utf-8')

# ── Config ────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000/api/v1/query"
COMPANY_SLUG = "craftsman_automation_ltd"
RESULTS_DIR = Path("tests/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
JSON_OUTPUT = RESULTS_DIR / f"eval_raw_results_mini_{TIMESTAMP}.json"
TXT_OUTPUT  = RESULTS_DIR / f"eval_raw_results_mini_{TIMESTAMP}.txt"

# ── Question Bank ─────────────────────────────────────────────────────────────
QUESTIONS = [
    # ── EXCEL ──
    {
        "id": 1,
        "section": "Excel",
        "difficulty": "Easy",
        "question": "What was the Net Profit reported by the company in FY26?",
        "expected_answer": "Net Profit in FY26 was ₹383.99 Cr — a recovery from ₹194.57 Cr in FY25 and the highest absolute net profit in the 10-year dataset.",
        "expected_source": ["craftsman_automation_ltd_excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 5,
        "section": "Excel",
        "difficulty": "Medium",
        "question": "Calculate the Operating Profit Margin for FY24 and FY25 and comment on the trend. OPM = Operating Profit / Sales × 100",
        "expected_answer": "FY24 OPM: 19.74%. FY25 OPM: 14.64%. OPM contracted sharply by ~510 bps despite 27.8% revenue growth — a significant margin deterioration.",
        "expected_source": ["craftsman_automation_ltd_excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 9,
        "section": "Excel",
        "difficulty": "Hard",
        "question": "In FY25, sales grew 27.8% YoY yet PBT fell 39.4% from FY24. Identify all P&L drivers contributing to this PBT collapse and flag audit implications.",
        "expected_answer": "Key drivers: OPM contracted from 19.74% to 14.64%; Interest rose from ₹174.54 Cr to ₹216.64 Cr; Other Income collapsed from ₹18.09 Cr to ₹0.30 Cr; Depreciation rose by ₹69.33 Cr. Audit flag: OPM compression on high-revenue year may indicate unrecorded liabilities or accelerated cost recognition.",
        "expected_source": ["craftsman_automation_ltd_excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },

    # ── CONCALL ──
    {
        "id": 16,
        "section": "Concall",
        "difficulty": "Easy",
        "question": "What was the total consolidated H1 FY23 revenue reported by the company, and by what percentage did it exceed H1 FY22?",
        "expected_answer": "H1 FY23 revenue was ₹1,447 crores, compared to ₹1,000 crores in H1 FY22 — a 44.7% increase.",
        "expected_source": ["craftsman_automation_ltd_concalls"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 20,
        "section": "Concall",
        "difficulty": "Medium",
        "question": "Calculate the Debt-to-EBITDA ratio for FY23 H1 as disclosed by management, and compare it to the prior full-year ratio. What does the trend indicate?",
        "expected_answer": "H1 FY23 Debt-to-EBITDA (annualised) = 1.08x, compared to 1.33x for full-year FY22. Trend indicates improving debt serviceability as EBITDA grew 31% YoY.",
        "expected_source": ["craftsman_automation_ltd_concalls"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 24,
        "section": "Concall",
        "difficulty": "Hard",
        "question": "Management claimed in FY23 Q1 that the company's annualised pre-tax ROCE was 26%, an improvement from 20% for the full prior year. However total debt increased by ₹50 crores QoQ. Identify and explain the apparent contradiction.",
        "expected_answer": "ROCE improved because EBIT grew and the company took cash discounts from creditors (enabled by credit rating upgrade), reducing net capital employed even as gross debt rose. The rise in short-term debt was working capital-driven, not capex-driven.",
        "expected_source": ["craftsman_automation_ltd_concalls"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },

    # ── PDF TEXT ──
    {
        "id": 31,
        "section": "PDF",
        "difficulty": "Easy",
        "question": "What specific operating model does the company's Chairman describe as its unique competitive differentiator in the Chairman's letter for FY22?",
        "expected_answer": "The Chairman describes a Company-within-Company model — all verticals run as independent profit-making enterprises while sharing common philosophies, best-practices, and facilities.",
        "expected_source": ["craftsman_automation_ltd_pdf_text"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 32,
        "section": "PDF",
        "difficulty": "Medium",
        "question": "In the company's FY22 MD&A, which specific financial ratio showed the highest year-on-year percentage change, and what two factors does management explicitly attribute to this change?",
        "expected_answer": "The Interest Coverage Ratio showed the highest change at +53% (from 4.17x in FY21 to 6.40x in FY22). Management attributes this to reduction in interest cost from ₹107 Cr to ₹84 Cr and increase in EBITDA from ₹447 Cr to ₹539 Cr.",
        "expected_source": ["craftsman_automation_ltd_pdf_text"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 33,
        "section": "PDF",
        "difficulty": "Hard",
        "question": "The company's FY22 auditor identified two Key Audit Matters. What are they, and for the derivative contracts KAM, what is the combined carrying value of derivative assets and liabilities?",
        "expected_answer": "Two KAMs: (1) Accounting for Derivative Contracts — derivative assets ₹855 Lakhs, liabilities ₹538 Lakhs. (2) Accounting for PPE. Hedge effectiveness testing requires an auditor's expert.",
        "expected_source": ["craftsman_automation_ltd_pdf_text"],
        "expected_citation_contains": ["Annual-Report"],
    },

    # ── IMAGES ──
    {
        "id": 47,
        "section": "Images",
        "difficulty": "Easy",
        "question": "In the About the company infographic page of the FY22 annual report, a donut chart shows the revenue split by business segment. What are the three business segments shown and their respective percentage contributions?",
        "expected_answer": "Automotive Powertrain: 52%, Industrial & Engineering: 28%, Automotive Aluminium: 20%.",
        "expected_source": ["craftsman_automation_ltd_images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 49,
        "section": "Images",
        "difficulty": "Medium",
        "question": "In the KPI Position section bar charts of the FY22 annual report, what is the trend in the Debt/EBITDA ratio over the five-year period shown FY18 to FY22?",
        "expected_answer": "FY18: 2.92x, FY19: 2.57x, FY20: 2.31x, FY21: 1.57x, FY22: 1.33x. Consistent downward improving trend — FY22 at 1.33x is the lowest in the five-year series.",
        "expected_source": ["craftsman_automation_ltd_images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 50,
        "section": "Images",
        "difficulty": "Hard",
        "question": "In the FY22 annual report, opening pages contain CAGR infographics showing growth from FY18 to FY22 across Revenue, EBIT, EBITDA, and PAT. The PAT CAGR of 49% is significantly higher than Revenue CAGR of 11%. What specific caveat is noted on the Revenue CAGR infographic that a CA must flag?",
        "expected_answer": "A footnote reads Excluding Excise Duty — the FY18 base figure excludes the pre-GST excise duty component, making the revenue CAGR comparison potentially understated. This means the PAT outperformance must be interpreted with this base effect in mind.",
        "expected_source": ["craftsman_automation_ltd_images"],
        "expected_citation_contains": ["Annual-Report"],
    },

    # ── CROSS-SOURCE ──
    {
        "id": 63,
        "section": "Cross",
        "difficulty": "Easy",
        "question": "In the FY22 Q4 earnings call, management guided total debt reduction of ₹100 Crores for FY23. What does the Excel Balance Sheet data show as the actual change in total borrowings in FY23 — was guidance met?",
        "expected_answer": "Q4 FY22 concall guided debt reduction from ₹713 Cr to ~₹613 Cr. Excel shows FY23 borrowings at ₹1,240.23 Cr — not only was the target missed, debt nearly doubled due to the DR Axion acquisition financing.",
        "expected_source": ["craftsman_automation_ltd_excel", "craftsman_automation_ltd_concalls"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "CraftsmanAutomation"],
    },
    {
        "id": 67,
        "section": "Cross",
        "difficulty": "Medium",
        "question": "The FY24 Chairman's letter describes business performance as consolidation and moderation in growth. Calculate actual revenue growth and PAT growth for FY24 from Excel and assess whether moderation is accurate.",
        "expected_answer": "Excel: FY24 revenue grew 39.8% and PAT grew 27.9%. A 40% revenue growth year being described as moderation is misleading — the moderation likely refers to margin compression, not topline growth.",
        "expected_source": ["craftsman_automation_ltd_excel", "craftsman_automation_ltd_pdf_text"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "Annual-Report"],
    },
    {
        "id": 72,
        "section": "Cross",
        "difficulty": "Hard",
        "question": "Management guided debt reduction as a priority across multiple concall years. The FY25 MD&A shows Debt-Equity Ratio improving to 0.59x due to QIP. Using Excel borrowings data across all years, did debt actually reduce in absolute terms?",
        "expected_answer": "Excel Borrowings: FY22 ₹799 Cr → FY23 ₹1,240 Cr → FY24 ₹1,754 Cr → FY25 ₹2,358 Cr → FY26 ₹3,623 Cr. Debt rose every single year in absolute terms. The FY25 D/E improvement is entirely driven by QIP equity raise, not debt reduction. Management's narrative is factually contradicted by Excel data.",
        "expected_source": ["craftsman_automation_ltd_excel", "craftsman_automation_ltd_concalls", "craftsman_automation_ltd_pdf_text"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "CraftsmanAutomation", "Annual-Report"],
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def fire_question(question: str, company_slug: str) -> dict:
    payload = {
        "question": question,
        "company_slug": company_slug,
        "year": None,
    }
    start = time.time()
    try:
        resp = requests.post(API_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        latency = round(time.time() - start, 2)
        data["latency_seconds"] = latency
        return data
    except Exception as e:
        latency = round(time.time() - start, 2)
        return {
            "answer": f"ERROR: {e}",
            "citations": [],
            "collections_searched": [],
            "agent_used": "error",
            "agent_trace": str(e),
            "chunks": [],
            "latency_seconds": latency,
        }

def check_routing_lenient(actual_sources: list, expected_sources: list) -> bool:
    return set(expected_sources).issubset(set(actual_sources))

def check_routing_strict(actual_sources: list, expected_sources: list) -> bool:
    return set(expected_sources) == set(actual_sources)

def check_citation(citations: list, expected_contains: list) -> bool:
    citation_filenames = []
    for c in citations:
        fname = c.get("filename", "")
        citation_filenames.append(fname)
        if "excel" in fname.lower():
            citation_filenames.append("Craftsman Auto.xlsx")
        elif "concall" in fname.lower():
            citation_filenames.append("CraftsmanAutomation")
        elif "pdf" in fname.lower():
            citation_filenames.append("Annual-Report")
        elif "images" in fname.lower():
            citation_filenames.append("Annual-Report")
            
    citation_str = " ".join(citation_filenames).lower()
    return any(term.lower() in citation_str for term in expected_contains)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  FinBot Mini Evaluation Run")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total questions: {len(QUESTIONS)}")
    print(f"{'='*60}\n")

    results = []
    section_stats = {}

    for i, q in enumerate(QUESTIONS, 1):
        section = q["section"]
        print(f"[{i:02d}/{len(QUESTIONS)}] {section} | {q['difficulty']} | Q{q['id']}: {q['question'][:70]}...")

        response = fire_question(q["question"], COMPANY_SLUG)

        routing_debug = response.get("routing_debug", {})
        raw_sources = response.get("collections_searched", [])
        fallback_fired = routing_debug.get("method", "") == "keyword_fallback"

        routing_lenient = check_routing_lenient(raw_sources, q["expected_source"])
        routing_strict = check_routing_strict(raw_sources, q["expected_source"])
        citation_correct = check_citation(response.get("citations", []), q["expected_citation_contains"])

        actual_chunk_metadata = []
        for c in response.get("chunks", []):
            if isinstance(c, dict) and "metadata" in c:
                meta = c["metadata"] or {}
                actual_chunk_metadata.append({
                    "filename": meta.get("filename", "unknown"),
                    "page": meta.get("page") or meta.get("sheet", "unknown"),
                    "source_type": meta.get("source_type", "unknown")
                })

        result = {
            "id": q["id"],
            "section": section,
            "difficulty": q["difficulty"],
            "question": q["question"],
            "expected_answer": q["expected_answer"],
            "expected_source": q["expected_source"],
            "expected_citation_contains": q["expected_citation_contains"],
            "actual_answer": response.get("answer", ""),
            "actual_sources": response.get("collections_searched", []),
            "actual_citations": response.get("citations", []),
            "actual_chunks": [c.get("content", "") for c in response.get("chunks", []) if isinstance(c, dict) and "content" in c],
            "actual_chunk_metadata": actual_chunk_metadata,
            "token_usage": response.get("token_usage", {}),
            "routing_debug": routing_debug,
            "agent_used": response.get("agent_used", ""),
            "latency_seconds": response.get("latency_seconds", 0),
            "routed_sources": raw_sources,
            "fallback_fired": fallback_fired,
            "routing_correct_lenient": routing_lenient,
            "routing_correct_strict": routing_strict,
            "routing_correct": routing_lenient,
            "citation_correct": citation_correct,
            "correct": None,
        }

        results.append(result)

        if section not in section_stats:
            section_stats[section] = {
                "total": 0, "routing_lenient": 0, "routing_strict": 0,
                "citation_correct": 0, "latency_total": 0, "fallback_fired": 0
            }
        section_stats[section]["total"] += 1
        section_stats[section]["routing_lenient"] += int(routing_lenient)
        section_stats[section]["routing_strict"] += int(routing_strict)
        section_stats[section]["fallback_fired"] += int(fallback_fired)
        section_stats[section]["citation_correct"] += int(citation_correct)
        section_stats[section]["latency_total"] += response.get("latency_seconds", 0)

        status = "PASS" if routing_strict else ("WARN" if routing_lenient else "FAIL")
        print(f"         Routing: {status} | Latency: {response.get('latency_seconds', 0)}s\n")

        jsonl_output = JSON_OUTPUT.with_suffix(".jsonl")
        with open(jsonl_output, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

        time.sleep(1)

    output = {
        "run_timestamp": TIMESTAMP,
        "total_questions": len(QUESTIONS),
        "company_slug": COMPANY_SLUG,
        "results": results,
    }

    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(TXT_OUTPUT, "w", encoding="utf-8") as f:
        f.write(f"FinBot Mini Evaluation Raw Results\nRun: {TIMESTAMP}\n{'='*80}\n\n")
        for r in results:
            f.write(f"Q{r['id']} [{r['section']}] [{r['difficulty']}]\n")
            f.write(f"Question: {r['question']}\n")
            f.write(f"Expected: {r['expected_answer']}\n")
            f.write(f"Actual:   {r['actual_answer']}\n")
            f.write(f"Routing:  {'✅' if r['routing_correct'] else '❌'} | Expected: {r['expected_source']} | Got: {r['actual_sources']}\n")
            f.write(f"Citation: {'✅' if r['citation_correct'] else '❌'}\n")
            f.write(f"Latency:  {r['latency_seconds']}s\n")
            f.write(f"{'-'*80}\n\n")

    print(f"\n{'='*60}")
    print(f"  EVALUATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Total questions: {len(results)}")
    print(f"  Results saved to:")
    print(f"  JSON: {JSON_OUTPUT}")
    print(f"  TXT:  {TXT_OUTPUT}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
