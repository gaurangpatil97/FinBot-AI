"""
FinBot Evaluation Scoring Script — score_eval.py
Reads raw eval results, runs RAGAS, and generates final scorecard.

Usage:
    python tests/questions/score_eval.py --input tests/results/eval_raw_results_TIMESTAMP.json

Steps before running:
    1. Run run_eval.py to generate raw results
    2. Open the raw results JSON
    3. For each question, set "correct": true or false based on manual review
    4. Save the JSON
    5. Run this script

Output:
    tests/results/eval_final_report_TIMESTAMP.json
    tests/results/eval_final_report_TIMESTAMP.txt
"""

import json
import argparse
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
RESULTS_DIR = Path("tests/results")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

RAGAS_AVAILABLE = True
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision,
    )
    from datasets import Dataset
except ImportError:
    RAGAS_AVAILABLE = False
    print("⚠️  RAGAS not installed or import failed. Skipping RAGAS metrics.")
    print("   Install with: pip install ragas datasets")


# ── Load Results ──────────────────────────────────────────────────────────────

def load_results(input_path: str) -> dict:
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Auto Metrics ──────────────────────────────────────────────────────────────

def compute_auto_metrics(results: list) -> dict:
    """Compute routing accuracy, citation accuracy, latency from results."""
    total = len(results)
    routing_correct = sum(1 for r in results if r.get("routing_correct", False))
    citation_correct = sum(1 for r in results if r.get("citation_correct", False))
    manual_correct = sum(1 for r in results if r.get("correct") is True)
    manual_total = sum(1 for r in results if r.get("correct") is not None)
    latencies = [r.get("latency_seconds", 0) for r in results]

    # Per section
    sections = {}
    for r in results:
        section = r.get("section", "Unknown")
        if section not in sections:
            sections[section] = {
                "total": 0,
                "routing_correct": 0,
                "citation_correct": 0,
                "correct": 0,
                "correct_total": 0,
                "latency_total": 0,
            }
        sections[section]["total"] += 1
        sections[section]["routing_correct"] += int(r.get("routing_correct", False))
        sections[section]["citation_correct"] += int(r.get("citation_correct", False))
        sections[section]["latency_total"] += r.get("latency_seconds", 0)
        if r.get("correct") is not None:
            sections[section]["correct_total"] += 1
            sections[section]["correct"] += int(r.get("correct", False))

    # Per difficulty
    difficulties = {}
    for r in results:
        diff = r.get("difficulty", "Unknown")
        if diff not in difficulties:
            difficulties[diff] = {"total": 0, "routing_correct": 0, "correct": 0, "correct_total": 0}
        difficulties[diff]["total"] += 1
        difficulties[diff]["routing_correct"] += int(r.get("routing_correct", False))
        if r.get("correct") is not None:
            difficulties[diff]["correct_total"] += 1
            difficulties[diff]["correct"] += int(r.get("correct", False))

    return {
        "total": total,
        "routing_accuracy": routing_correct / total if total else 0,
        "routing_correct": routing_correct,
        "citation_accuracy": citation_correct / total if total else 0,
        "citation_correct": citation_correct,
        "answer_correctness": manual_correct / manual_total if manual_total else None,
        "answer_correct": manual_correct,
        "answer_total_reviewed": manual_total,
        "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
        "min_latency": min(latencies) if latencies else 0,
        "max_latency": max(latencies) if latencies else 0,
        "sections": sections,
        "difficulties": difficulties,
    }


# ── RAGAS ─────────────────────────────────────────────────────────────────────

def run_ragas(results: list) -> dict:
    """Run RAGAS metrics on results that have chunks."""
    if not RAGAS_AVAILABLE:
        return {"error": "RAGAS not available"}

    # Build dataset — only include questions that have chunks and expected answers
    questions = []
    answers = []
    contexts = []
    ground_truths = []

    skipped = 0
    for r in results:
        chunks = r.get("actual_chunks", [])
        if not chunks:
            skipped += 1
            continue
        if not r.get("actual_answer") or not r.get("expected_answer"):
            skipped += 1
            continue

        questions.append(r["question"])
        answers.append(r["actual_answer"])
        contexts.append([c for c in chunks if isinstance(c, str)])
        ground_truths.append(r["expected_answer"])

    if not questions:
        return {"error": "No questions with chunks available for RAGAS"}

    print(f"\n  Running RAGAS on {len(questions)} questions ({skipped} skipped — no chunks)...")

    try:
        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        })

        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_recall,
                context_precision,
            ],
        )

        def _safe_float(val):
            if val is None:
                return None
            if isinstance(val, list):
                val = [v for v in val if v is not None]
                return round(sum(val) / len(val), 4) if val else None
            return round(float(val), 4)

        return {
            "questions_evaluated": len(questions),
            "questions_skipped": skipped,
            "faithfulness": _safe_float(result["faithfulness"]),
            "answer_relevancy": _safe_float(result["answer_relevancy"]),
            "context_recall": _safe_float(result["context_recall"]),
            "context_precision": _safe_float(result["context_precision"]),
        }

    except Exception as e:
        return {"error": str(e)}


# ── Report Generation ─────────────────────────────────────────────────────────

def generate_report(auto_metrics: dict, ragas_metrics: dict, raw_data: dict) -> str:
    """Generate a clean text report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  FINBOT EVALUATION FINAL REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Source: {raw_data.get('run_timestamp', 'unknown')}")
    lines.append(f"  Company: {raw_data.get('company_slug', 'unknown')}")
    lines.append("=" * 70)

    lines.append("\n── SYSTEM OVERVIEW ──────────────────────────────────────────────────")
    lines.append(f"  Total questions evaluated: {auto_metrics['total']}")
    lines.append(f"  Questions manually reviewed: {auto_metrics['answer_total_reviewed']}")

    lines.append("\n── AUTO-SCORED METRICS ──────────────────────────────────────────────")
    lines.append(f"  Routing Accuracy:   {auto_metrics['routing_correct']}/{auto_metrics['total']} = {auto_metrics['routing_accuracy']*100:.1f}%")
    lines.append(f"  Citation Accuracy:  {auto_metrics['citation_correct']}/{auto_metrics['total']} = {auto_metrics['citation_accuracy']*100:.1f}%")

    if auto_metrics["answer_correctness"] is not None:
        lines.append(f"  Answer Correctness: {auto_metrics['answer_correct']}/{auto_metrics['answer_total_reviewed']} = {auto_metrics['answer_correctness']*100:.1f}%")
    else:
        lines.append(f"  Answer Correctness: NOT YET REVIEWED (set 'correct': true/false in JSON)")

    lines.append(f"\n  Latency:")
    lines.append(f"    Average: {auto_metrics['avg_latency']:.2f}s")
    lines.append(f"    Min:     {auto_metrics['min_latency']:.2f}s")
    lines.append(f"    Max:     {auto_metrics['max_latency']:.2f}s")

    lines.append("\n── RAGAS METRICS ────────────────────────────────────────────────────")
    if "error" in ragas_metrics:
        lines.append(f"  ⚠️  {ragas_metrics['error']}")
    else:
        lines.append(f"  Questions evaluated: {ragas_metrics.get('questions_evaluated', 0)}")
        lines.append(f"  Questions skipped:   {ragas_metrics.get('questions_skipped', 0)} (no chunks)")
        lines.append(f"  Faithfulness:        {ragas_metrics.get('faithfulness', 'N/A')}")
        lines.append(f"  Answer Relevancy:    {ragas_metrics.get('answer_relevancy', 'N/A')}")
        lines.append(f"  Context Recall:      {ragas_metrics.get('context_recall', 'N/A')}")
        lines.append(f"  Context Precision:   {ragas_metrics.get('context_precision', 'N/A')}")

    lines.append("\n── PER SECTION BREAKDOWN ────────────────────────────────────────────")
    lines.append(f"  {'Section':<12} {'Total':>6} {'Routing':>10} {'Citation':>10} {'Correct':>10} {'Avg Lat':>10}")
    lines.append(f"  {'-'*62}")

    for section, stats in auto_metrics["sections"].items():
        n = stats["total"]
        routing_pct = stats["routing_correct"] / n * 100
        citation_pct = stats["citation_correct"] / n * 100
        avg_lat = stats["latency_total"] / n

        if stats["correct_total"] > 0:
            correct_str = f"{stats['correct']}/{stats['correct_total']} ({stats['correct']/stats['correct_total']*100:.0f}%)"
        else:
            correct_str = "not reviewed"

        lines.append(
            f"  {section:<12} {n:>6} "
            f"{stats['routing_correct']}/{n} ({routing_pct:.0f}%):>10 "
            f"{stats['citation_correct']}/{n} ({citation_pct:.0f}%):>10 "
            f"{correct_str:>10} "
            f"{avg_lat:.1f}s:>10"
        )

    lines.append("\n── PER DIFFICULTY BREAKDOWN ─────────────────────────────────────────")
    for diff, stats in auto_metrics["difficulties"].items():
        n = stats["total"]
        routing_pct = stats["routing_correct"] / n * 100
        if stats["correct_total"] > 0:
            correct_str = f"{stats['correct']}/{stats['correct_total']} ({stats['correct']/stats['correct_total']*100:.0f}%)"
        else:
            correct_str = "not reviewed"
        lines.append(f"  {diff:<10} Routing: {stats['routing_correct']}/{n} ({routing_pct:.0f}%) | Correct: {correct_str}")

    lines.append("\n── FAILURE ANALYSIS ─────────────────────────────────────────────────")
    results = raw_data.get("results", [])
    routing_failures = [r for r in results if not r.get("routing_correct", False)]
    citation_failures = [r for r in results if not r.get("citation_correct", False)]
    answer_failures = [r for r in results if r.get("correct") is False]

    lines.append(f"\n  Routing Failures ({len(routing_failures)}):")
    for r in routing_failures[:10]:
        lines.append(f"    Q{r['id']} [{r['section']}]: Expected {r['expected_source']} | Got {r['actual_sources']}")
    if len(routing_failures) > 10:
        lines.append(f"    ... and {len(routing_failures)-10} more")

    lines.append(f"\n  Citation Failures ({len(citation_failures)}):")
    for r in citation_failures[:10]:
        lines.append(f"    Q{r['id']} [{r['section']}]: {r['question'][:60]}...")
    if len(citation_failures) > 10:
        lines.append(f"    ... and {len(citation_failures)-10} more")

    if answer_failures:
        lines.append(f"\n  Answer Failures ({len(answer_failures)}):")
        for r in answer_failures[:10]:
            lines.append(f"    Q{r['id']} [{r['section']}] [{r['difficulty']}]: {r['question'][:60]}...")

    lines.append("\n── SUMMARY ──────────────────────────────────────────────────────────")
    lines.append(f"  Routing Accuracy:   {auto_metrics['routing_accuracy']*100:.1f}%")
    lines.append(f"  Citation Accuracy:  {auto_metrics['citation_accuracy']*100:.1f}%")
    if auto_metrics["answer_correctness"] is not None:
        lines.append(f"  Answer Correctness: {auto_metrics['answer_correctness']*100:.1f}%")
    if "faithfulness" in ragas_metrics:
        lines.append(f"  Faithfulness:       {ragas_metrics['faithfulness']}")
        lines.append(f"  Context Recall:     {ragas_metrics['context_recall']}")
        lines.append(f"  Context Precision:  {ragas_metrics['context_precision']}")
    lines.append(f"  Avg Latency:        {auto_metrics['avg_latency']:.2f}s")
    lines.append("=" * 70)

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Score FinBot eval results")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to eval_raw_results JSON file"
    )
    parser.add_argument(
        "--skip-ragas",
        action="store_true",
        help="Skip RAGAS scoring (faster, use if RAGAS not installed)"
    )
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  FinBot Evaluation Scoring")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Load results
    print(f"  Loading results from: {args.input}")
    raw_data = load_results(args.input)
    results = raw_data.get("results", [])
    print(f"  Loaded {len(results)} results\n")

    # Check manual review status
    reviewed = sum(1 for r in results if r.get("correct") is not None)
    print(f"  Manual review status: {reviewed}/{len(results)} questions reviewed")
    if reviewed == 0:
        print("  ⚠️  No manual reviews found. Answer Correctness will be skipped.")
        print("  Add 'correct': true/false to each result in the JSON and re-run.\n")

    # Auto metrics
    print("  Computing auto metrics...")
    auto_metrics = compute_auto_metrics(results)

    # RAGAS
    if args.skip_ragas:
        print("  Skipping RAGAS (--skip-ragas flag set)")
        ragas_metrics = {"error": "Skipped by user"}
    else:
        ragas_metrics = run_ragas(results)

    # Generate report
    print("\n  Generating report...")
    report_text = generate_report(auto_metrics, ragas_metrics, raw_data)

    # Save outputs
    json_output = RESULTS_DIR / f"eval_final_report_{TIMESTAMP}.json"
    txt_output = RESULTS_DIR / f"eval_final_report_{TIMESTAMP}.txt"

    final_output = {
        "generated_at": TIMESTAMP,
        "source_file": args.input,
        "auto_metrics": auto_metrics,
        "ragas_metrics": ragas_metrics,
    }

    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    with open(txt_output, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(report_text)
    print(f"\n  Saved to:")
    print(f"  JSON: {json_output}")
    print(f"  TXT:  {txt_output}\n")


if __name__ == "__main__":
    main()