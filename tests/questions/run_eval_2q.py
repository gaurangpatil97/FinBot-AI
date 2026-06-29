"""
FinBot Evaluation Script — run_eval_2q.py
Fires Q8 and Q64 at the FinBot API and saves raw results.
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
JSON_OUTPUT = RESULTS_DIR / f"eval_raw_results_targeted_{TIMESTAMP}.json"
TXT_OUTPUT  = RESULTS_DIR / f"eval_raw_results_targeted_{TIMESTAMP}.txt"

# ── Question Bank ─────────────────────────────────────────────────────────────
QUESTIONS = [
  {
    'id': 8,
    'section': 'Excel',
    'difficulty': 'Medium',
    'question': 'Compute the Interest Coverage Ratio for FY22 and FY25 and evaluate debt serviceability. ICR = Operating Profit / Interest',
    'expected_answer': 'FY22 ICR: 6.34x. FY25 ICR: 3.85x. ICR has deteriorated significantly as debt servicing costs outpaced operating profit growth.',
    'expected_source': ['craftsman_automation_ltd_excel'],
    'expected_citation_contains': ['Craftsman Auto.xlsx']
  },
  {
    'id': 64,
    'section': 'Cross',
    'difficulty': 'Easy',
    'question': 'The FY23 MD&A states the Interest Coverage Ratio declined from 6.40x to 5.74x due to increased interest cost. Verify this using the Excel P&L data — does the reported interest figure match?',
    'expected_answer': 'Excel shows FY22 Interest = ₹84.22 Cr, FY23 Interest = ₹117 Cr — confirming the MD&A narrative. ICR from Excel: FY22 = 6.40x confirmed. Slight discrepancy in FY23 ICR suggests EBITDA definition differs between Excel and MD&A.',
    'expected_source': ['craftsman_automation_ltd_excel', 'craftsman_automation_ltd_pdf_text'],
    'expected_citation_contains': ['Craftsman Auto.xlsx', 'Annual-Report']
  }
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
    print(f"  FinBot 2-Question Targeted Run")
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
        f.write(f"FinBot 2-Question Raw Results\nRun: {TIMESTAMP}\n{'='*80}\n\n")
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
