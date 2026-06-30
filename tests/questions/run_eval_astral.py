"""
FinBot Evaluation Script — run_eval_astral.py
Fires all 77 evaluation questions at the FinBot API and saves raw results for Astral Ltd.

Usage:
    python run_eval_astral.py
"""

import json
import time
import requests
import sys
from datetime import datetime
from pathlib import Path

# Import QUESTIONS from Astral_questions_run_eval
from Astral_questions_run_eval import QUESTIONS

# Force UTF-8 stdout for Windows
sys.stdout.reconfigure(encoding='utf-8')

# ── Config ────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000/api/v1/query"
COMPANY_SLUG = "astral_ltd"
COMPANY_NAME = "Astral Ltd"
RESULTS_DIR = Path("tests/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
JSON_OUTPUT = RESULTS_DIR / f"eval_raw_results_{COMPANY_SLUG}_{TIMESTAMP}.json"
TXT_OUTPUT  = RESULTS_DIR / f"eval_raw_results_{COMPANY_SLUG}_{TIMESTAMP}.txt"


# ── Functions ─────────────────────────────────────────────────────────────────

def fire_question(question: str, company_slug: str) -> dict:
    payload = {
        "question": question,
        "company_slug": company_slug
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=90)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text}")
            return {}
    except Exception as e:
        print(f"Failed to fire question: {e}")
        return {}


def check_routing_lenient(raw_sources: list, expected_source: list) -> bool:
    """True if there is ANY overlap between raw_sources and expected_source."""
    if not expected_source:
        return True
    return any(src in raw_sources for src in expected_source)


def check_routing_strict(raw_sources: list, expected_source: list) -> bool:
    """True if raw_sources matches expected_source exactly."""
    if not expected_source:
        return not raw_sources
    return sorted(raw_sources) == sorted(expected_source)


def check_citation(actual_citations: list, expected_contains: list) -> bool:
    if not expected_contains:
        return True
    if not actual_citations:
        return False

    citation_filenames = []
    for citation in actual_citations:
        if isinstance(citation, dict):
            fname = citation.get("source_url", "") or citation.get("filename", "") or citation.get("source_uri", "")
            if fname.startswith("http") or fname.startswith("file") or "\\" in fname or "/" in fname:
                fname = Path(fname).name
        else:
            fname = Path(str(citation)).name
        citation_filenames.append(fname)
        if "excel" in fname.lower():
            citation_filenames.append("Astral_Ltd.xlsx")
        elif "concall" in fname.lower():
            citation_filenames.append("Astral_Ltd")
        elif "pdf" in fname.lower():
            citation_filenames.append("Astral_Ltd")
        elif "images" in fname.lower():
            citation_filenames.append("Astral_Ltd")
            
    citation_str = " ".join(citation_filenames).lower()
    return any(term.lower() in citation_str for term in expected_contains)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"  FinBot Evaluation Run ({COMPANY_NAME})")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total questions: {len(QUESTIONS)}")
    print(f"{'='*60}\n")

    results = []
    section_stats = {}

    for i, q in enumerate(QUESTIONS, 1):
        section = q["section"]
        print(f"[{i:02d}/{len(QUESTIONS)}] {section} | {q['difficulty']} | Q{q['id']}: {q['question'][:70]}...")

        # Fire question
        response = fire_question(q["question"], COMPANY_SLUG)

        # Auto-score routing and citation
        routing_debug = response.get("routing_debug", {})
        raw_sources = response.get("collections_searched", [])
        fallback_fired = routing_debug.get("method", "") == "keyword_fallback"

        routing_lenient = check_routing_lenient(raw_sources, q["expected_source"])
        routing_strict = check_routing_strict(raw_sources, q["expected_source"])

        citation_correct = check_citation(
            response.get("citations", []),
            q["expected_citation_contains"]
        )

        # Extract chunk metadata separately
        actual_chunk_metadata = []
        for c in response.get("chunks", []):
            if isinstance(c, dict) and "metadata" in c:
                meta = c["metadata"] or {}
                actual_chunk_metadata.append({
                    "filename": meta.get("filename", "unknown"),
                    "page": meta.get("page") or meta.get("sheet", "unknown"),
                    "source_type": meta.get("source_type", "unknown")
                })

        # Build result record
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
            "routing_correct": routing_lenient,  # Keep for backwards compat if needed
            "citation_correct": citation_correct,
            "correct": None,  # To be filled manually
        }

        results.append(result)

        # Track section stats
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

        # Incrementally persist to JSONL
        jsonl_output = JSON_OUTPUT.with_suffix(".jsonl")
        with open(jsonl_output, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

        # Small delay to avoid rate limits
        time.sleep(1)

    # ── Save JSON ──────────────────────────────────────────────────────────────
    output = {
        "run_timestamp": TIMESTAMP,
        "total_questions": len(QUESTIONS),
        "company_slug": COMPANY_SLUG,
        "results": results,
    }

    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # ── Save TXT ───────────────────────────────────────────────────────────────
    with open(TXT_OUTPUT, "w", encoding="utf-8") as f:
        f.write(f"FinBot Evaluation Raw Results\n")
        f.write(f"Run: {TIMESTAMP}\n")
        f.write(f"{'='*80}\n\n")

        for r in results:
            f.write(f"Q{r['id']} [{r['section']}] [{r['difficulty']}]\n")
            f.write(f"Question: {r['question']}\n")
            f.write(f"Expected: {r['expected_answer']}\n")
            f.write(f"Actual:   {r['actual_answer']}\n")
            f.write(f"Routing:  {'✅' if r['routing_correct'] else '❌'} | Expected: {r['expected_source']} | Got: {r['actual_sources']}\n")
            f.write(f"Citation: {'✅' if r['citation_correct'] else '❌'}\n")
            f.write(f"Latency:  {r['latency_seconds']}s\n")
            f.write(f"Correct:  [FILL MANUALLY: true/false]\n")
            f.write(f"{'-'*80}\n\n")

        # ── Auto-scored summary ────────────────────────────────────────────────
        f.write(f"\n{'='*80}\n")
        f.write(f"AUTO-SCORED SUMMARY (Routing + Citation + Latency)\n")
        f.write(f"{'='*80}\n\n")

        total_lenient = sum(1 for r in results if r["routing_correct_lenient"])
        total_strict = sum(1 for r in results if r["routing_correct_strict"])
        total_fallback = sum(1 for r in results if r.get("fallback_fired"))
        total_citation = sum(1 for r in results if r["citation_correct"])
        avg_latency = sum(r["latency_seconds"] for r in results) / len(results)

        f.write(f"Routing Accuracy (Lenient): {total_lenient}/{len(results)} = {total_lenient/len(results)*100:.1f}%\n")
        f.write(f"Routing Accuracy (Strict):  {total_strict}/{len(results)} = {total_strict/len(results)*100:.1f}%\n")
        f.write(f"Total Fallbacks Fired:      {total_fallback}\n")
        f.write(f"Overall Citation Accuracy:  {total_citation}/{len(results)} = {total_citation/len(results)*100:.1f}%\n")
        f.write(f"Average Latency:            {avg_latency:.2f}s\n\n")

        f.write(f"Per Section:\n")
        for section, stats in section_stats.items():
            n = stats["total"]
            l_pct = stats["routing_lenient"] / n * 100
            s_pct = stats["routing_strict"] / n * 100
            c_pct = stats["citation_correct"] / n * 100
            avg_lat = stats["latency_total"] / n
            f.write(f"  {section:<10} Routing: {stats['routing_lenient']}/{n} lenient ({l_pct:.0f}%), {stats['routing_strict']}/{n} strict ({s_pct:.0f}%) | Fallbacks: {stats['fallback_fired']} | Citation: {stats['citation_correct']}/{n} ({c_pct:.0f}%) | Avg Latency: {avg_lat:.1f}s\n")

    # ── Print summary ──────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  EVALUATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Total questions:   {len(results)}")
    print(f"  Routing (Lenient): {total_lenient}/{len(results)} ({total_lenient/len(results)*100:.1f}%)")
    print(f"  Routing (Strict):  {total_strict}/{len(results)} ({total_strict/len(results)*100:.1f}%)")
    print(f"  Fallbacks fired:   {total_fallback}")
    print(f"  Citation accuracy: {total_citation}/{len(results)} ({total_citation/len(results)*100:.1f}%)")
    print(f"  Avg latency:       {avg_latency:.2f}s")
    print(f"\n  Results saved to:")
    print(f"  JSON: {JSON_OUTPUT}")
    print(f"  TXT:  {TXT_OUTPUT}")
    print(f"\n  Next steps:")
    print(f"  1. Open {TXT_OUTPUT} and mark correct: true/false for each answer")
    print(f"  2. Update the JSON file with your manual correct values")
    print(f"  3. Run score_eval.py to get full metrics including RAGAS")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
