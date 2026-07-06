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
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 stdout for Windows
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

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
    manual_correct = sum(1 for r in results if r.get("correct") is True or r.get("correct") == 1)
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
            sections[section]["correct"] += int(r.get("correct") is True or r.get("correct") == 1)

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
            difficulties[diff]["correct"] += int(r.get("correct") is True or r.get("correct") == 1)

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


# ── Chunk Metrics ─────────────────────────────────────────────────────────────

def run_chunk_metrics(results: list) -> dict:
    precisions = []
    recalls = []
    f1s = []
    count = 0

    for r in results:
        expected = r.get("expected_citation_contains")
        meta = r.get("actual_chunk_metadata")
        if not expected or not meta:
            continue

        k = len(meta)
        if k == 0:
            continue

        # Normalize filenames in metadata to support collection names
        normalized_meta = []
        for m in meta:
            fname = m.get("filename", "")
            norm_names = [fname]
            if "excel" in fname.lower():
                norm_names.append("Craftsman Auto.xlsx")
            elif "concall" in fname.lower():
                norm_names.append("CraftsmanAutomation")
            elif "pdf" in fname.lower():
                norm_names.append("Annual-Report")
            elif "images" in fname.lower():
                norm_names.append("Annual-Report")
            normalized_meta.append(norm_names)

        hits_expected = sum(
            1 for exp in expected
            if any(any(exp.lower() in name.lower() for name in norm_names) for norm_names in normalized_meta)
        )

        precision = len([norm_names for norm_names in normalized_meta if any(any(exp.lower() in name.lower() for name in norm_names) for exp in expected)]) / k
        recall = hits_expected / len(expected)
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        count += 1

    if count == 0:
        return {
            "avg_precision_at_k": 0.0,
            "avg_recall_at_k": 0.0,
            "avg_f1_at_k": 0.0,
            "questions_evaluated": 0
        }

    return {
        "avg_precision_at_k": round(sum(precisions) / count, 4),
        "avg_recall_at_k": round(sum(recalls) / count, 4),
        "avg_f1_at_k": round(sum(f1s) / count, 4),
        "questions_evaluated": count
    }


# ── Completeness Judge ────────────────────────────────────────────────────────

def judge_binary_correctness(question: str, expected_answer: str, actual_answer: str, openai_api_key: str) -> int:
    if not openai_api_key:
        return 0
    try:
        import openai
        client = openai.OpenAI(api_key=openai_api_key)
        system_prompt = (
            "You are an evaluation judge. Compare the actual answer against the expected answer strictly on factual and numerical correctness.\n"
            "Key figures, numbers, percentages, and named entities must match exactly. Ignore differences in phrasing, extra elaboration, or formatting.\n"
            "Return exactly 1 if all key facts and figures in expected_answer are correctly present and accurate in actual_answer, or 0 if any key fact/figure is missing, wrong, or contradicted.\n"
            "No partial credit. Output must be a single character: either 1 or 0, and nothing else."
        )
        user_message = f"Question: {question}\nExpected Answer: {expected_answer}\nActual Answer: {actual_answer}"
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0,
            max_tokens=10
        )
        content = response.choices[0].message.content.strip()
        return 1 if "1" in content else 0
    except Exception as e:
        print(f"⚠️ Error in judge_binary_correctness: {e}")
        return 0

def run_completeness_judge(results: list, openai_api_key: str) -> dict:
    if not openai_api_key:
        return {"error": "OpenAI API key not provided"}

    import openai
    client = openai.OpenAI(api_key=openai_api_key)

    scores = []
    count = 0
    binary_correct_count = 0
    total_evaluated = 0

    system_prompt = (
        "You are an evaluation judge. Given a reference answer and a model's actual answer, "
        "score how completely the model's answer covers all key points in the reference answer.\n\n"
        "Return ONLY a JSON object like: {\"score\": 0.85, \"reasoning\": \"one sentence\"}\n\n"
        "Score from 0.0 to 1.0:\n"
        "- 1.0 = all key points covered\n"
        "- 0.5 = roughly half the key points covered  \n"
        "- 0.0 = none of the key points covered"
    )

    for r in results:
        actual = r.get("actual_answer")
        expected = r.get("expected_answer")
        question = r.get("question")
        if not actual or not expected:
            continue

        user_message = f"Reference answer: {expected}\n\nModel answer: {actual}"

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            score = float(data["score"])
            scores.append(score)
            count += 1
        except Exception as e:
            print(f"⚠️ Error running completeness judge for question {r.get('id')}: {e}")
            score = 0.0

        # Run strict binary correctness judge
        binary_score = judge_binary_correctness(question, expected, actual, openai_api_key)
        r["correct"] = binary_score
        binary_correct_count += binary_score
        total_evaluated += 1

    if count == 0:
        return {
            "answer_completeness": 0.0,
            "questions_evaluated": 0,
            "binary_correct": 0,
            "binary_total": 0
        }

    return {
        "answer_completeness": round(sum(scores) / count, 4),
        "questions_evaluated": count,
        "binary_correct": binary_correct_count,
        "binary_total": total_evaluated
    }


# ── Cost Metrics ──────────────────────────────────────────────────────────────

def compute_cost_metrics(results: list) -> dict:
    costs = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    count = 0

    for r in results:
        usage = r.get("token_usage")
        if not usage or not isinstance(usage, dict):
            continue

        prompt_tokens = usage.get("prompt_tokens", 0) or 0
        completion_tokens = usage.get("completion_tokens", 0) or 0
        
        cost = (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.60 / 1_000_000)
        costs.append(cost)
        
        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens
        total_tokens += (prompt_tokens + completion_tokens)
        count += 1

    if count == 0:
        return {
            "avg_cost_per_query": 0.0,
            "total_cost": 0.0,
            "min_cost": 0.0,
            "max_cost": 0.0,
            "total_tokens": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "queries_with_token_usage": 0
        }

    return {
        "avg_cost_per_query": round(sum(costs) / count, 6),
        "total_cost": round(sum(costs), 6),
        "min_cost": round(min(costs), 6),
        "max_cost": round(max(costs), 6),
        "total_tokens": total_tokens,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "queries_with_token_usage": count
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

    print(f"\n  Running RAGAS on {len(questions)} questions...")

    try:
        from ragas.run_config import RunConfig
        import numpy as np
        from langchain_openai import ChatOpenAI
        from ragas.llms import LangchainLLMWrapper
        
        dataset = Dataset.from_dict({
            "user_input": questions,
            "response": answers,
            "retrieved_contexts": contexts,
            "reference": ground_truths,
        })

        run_config = RunConfig(max_workers=4, max_retries=10)
        eval_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4.1-mini"))
        
        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_recall,
                context_precision,
            ],
            raise_exceptions=False,
            llm=eval_llm,
            run_config=run_config
        )

        df = result.to_pandas()
        
        nan_counts = {
            "faithfulness": df["faithfulness"].isna().sum() if "faithfulness" in df else len(df),
            "answer_relevancy": df["answer_relevancy"].isna().sum() if "answer_relevancy" in df else len(df),
            "context_recall": df["context_recall"].isna().sum() if "context_recall" in df else len(df),
            "context_precision": df["context_precision"].isna().sum() if "context_precision" in df else len(df)
        }
        
        print("\n--- NaN ROW COUNTS ---")
        for k, v in nan_counts.items():
            print(f"{k}: {v}")
        print("----------------------\n")

        def _safe_nanmean(col_name):
            if col_name not in df.columns:
                return None
            val = np.nanmean(df[col_name])
            if np.isnan(val):
                return None
            return round(float(val), 4)

        faithfulness_score = _safe_nanmean("faithfulness")
        hallucination_rate = None
        if faithfulness_score is not None:
            hallucination_rate = round((1 - faithfulness_score) * 100, 2)

        return {
            "questions_evaluated": len(questions),
            "questions_skipped": skipped,
            "faithfulness": faithfulness_score,
            "answer_relevancy": _safe_nanmean("answer_relevancy"),
            "context_recall": _safe_nanmean("context_recall"),
            "context_precision": _safe_nanmean("context_precision"),
            "hallucination_rate_percent": hallucination_rate,
        }

    except Exception as e:
        return {"error": str(e)}


# ── Report Generation ─────────────────────────────────────────────────────────

def generate_report(auto_metrics: dict, ragas_metrics: dict, chunk_metrics: dict, completeness_metrics: dict, cost_metrics: dict, raw_data: dict) -> str:
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

    if "binary_correct" in completeness_metrics and completeness_metrics["binary_total"] > 0:
        bc = completeness_metrics["binary_correct"]
        bt = completeness_metrics["binary_total"]
        pct = (bc / bt) * 100
        lines.append(f"  Strict Binary Correctness: {bc}/{bt} = {pct:.1f}%")

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
        lines.append(f"  Hallucination Rate:  {ragas_metrics.get('hallucination_rate_percent', 'N/A')}%")

    lines.append("\n── CHUNK & RETRIEVAL METRICS ────────────────────────────────────────")
    lines.append(f"  Precision@K:        {chunk_metrics.get('avg_precision_at_k', 'N/A')}")
    lines.append(f"  Recall@K:           {chunk_metrics.get('avg_recall_at_k', 'N/A')}")
    lines.append(f"  F1@K:               {chunk_metrics.get('avg_f1_at_k', 'N/A')}")
    lines.append(f"  Questions Evaluated: {chunk_metrics.get('questions_evaluated', 0)}")

    lines.append("\n── COMPLETENESS & COST METRICS ──────────────────────────────────────")
    if "error" in completeness_metrics:
        lines.append(f"  Answer Completeness: {completeness_metrics['error']}")
    else:
        lines.append(f"  Answer Completeness: {completeness_metrics.get('answer_completeness', 'N/A')} (gpt-4o-mini judge)")
    
    lines.append(f"  Total Cost:         ${cost_metrics.get('total_cost', 0.0):.6f}")
    lines.append(f"  Avg Cost/Query:     ${cost_metrics.get('avg_cost_per_query', 0.0):.6f}")
    lines.append(f"  Min Cost/Query:     ${cost_metrics.get('min_cost', 0.0):.6f}")
    lines.append(f"  Max Cost/Query:     ${cost_metrics.get('max_cost', 0.0):.6f}")
    lines.append(f"  Total Tokens:       {cost_metrics.get('total_tokens', 0)}")

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
    if "binary_correct" in completeness_metrics and completeness_metrics["binary_total"] > 0:
        bc = completeness_metrics["binary_correct"]
        bt = completeness_metrics["binary_total"]
        pct = (bc / bt) * 100
        lines.append(f"  Strict Binary Correctness: {bc}/{bt} correct ({pct:.1f}%)")
    if "faithfulness" in ragas_metrics:
        lines.append(f"  Faithfulness:       {ragas_metrics['faithfulness']}")
        lines.append(f"  Context Recall:     {ragas_metrics['context_recall']}")
        lines.append(f"  Context Precision:  {ragas_metrics['context_precision']}")
        lines.append(f"  Hallucination Rate: {ragas_metrics.get('hallucination_rate_percent', 'N/A')}%")
    if "avg_f1_at_k" in chunk_metrics:
        lines.append(f"  Retrieval F1@K:     {chunk_metrics['avg_f1_at_k']}")
    if "answer_completeness" in completeness_metrics:
        lines.append(f"  Completeness:       {completeness_metrics['answer_completeness']}")
    lines.append(f"  Avg Cost/Query:     ${cost_metrics.get('avg_cost_per_query', 0.0):.6f}")
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
    parser.add_argument(
        "--completeness",
        action="store_true",
        help="Run Answer Completeness judge (LLM-as-judge, costs money)"
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

    # Chunk metrics
    print("  Computing chunk metrics...")
    chunk_metrics = run_chunk_metrics(results)

    # Cost metrics
    print("  Computing cost metrics...")
    cost_metrics = compute_cost_metrics(results)

    # Completeness metrics (optional)
    if args.completeness:
        print("  Running completeness judge...")
        import os
        api_key = os.getenv("OPENAI_API_KEY", "")
        completeness_metrics = run_completeness_judge(results, api_key)
        # Re-compute auto metrics so it displays the LLM-populated correctness results
        auto_metrics = compute_auto_metrics(results)
    else:
        completeness_metrics = {"error": "Skipped (pass --completeness flag to run)"}

    # RAGAS
    if args.skip_ragas:
        print("  Skipping RAGAS (--skip-ragas flag set)")
        ragas_metrics = {"error": "Skipped by user"}
    else:
        ragas_metrics = run_ragas(results)

    # Generate report
    print("\n  Generating report...")
    report_text = generate_report(
        auto_metrics=auto_metrics,
        ragas_metrics=ragas_metrics,
        chunk_metrics=chunk_metrics,
        completeness_metrics=completeness_metrics,
        cost_metrics=cost_metrics,
        raw_data=raw_data
    )

    # Save outputs
    json_output = RESULTS_DIR / f"eval_final_report_{TIMESTAMP}.json"
    txt_output = RESULTS_DIR / f"eval_final_report_{TIMESTAMP}.txt"

    final_output = {
        "generated_at": TIMESTAMP,
        "source_file": args.input,
        "auto_metrics": auto_metrics,
        "ragas_metrics": ragas_metrics,
        "chunk_metrics": chunk_metrics,
        "completeness_metrics": completeness_metrics,
        "cost_metrics": cost_metrics,
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