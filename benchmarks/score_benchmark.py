import json
import argparse
import sys
import os
from pathlib import Path

# Force UTF-8 stdout for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Load .env from root
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

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

def parse_args():
    parser = argparse.ArgumentParser(description="Score FinBot benchmarks")
    parser.add_argument(
        "--run-name",
        required=True,
        help="Name of the run, e.g. run_001"
    )
    parser.add_argument(
        "--ragas",
        action="store_true",
        help="Run RAGAS evaluation metrics (faithfulness, relevancy, recall, precision)"
    )
    parser.add_argument(
        "--company",
        choices=["astral_ltd", "craftsman_automation_ltd"],
        help="Optional company to filter processing. If omitted, all companies in the run are processed."
    )
    return parser.parse_args()

def check_routing(actual_routing, expected_routing, company_slug=None):
    if not expected_routing:
        return not actual_routing
        
    if isinstance(expected_routing, str):
        expected_list = [expected_routing]
    else:
        expected_list = list(expected_routing)
        
    if company_slug and company_slug != "astral_ltd":
        expected_list = [str(x).replace("astral_ltd", company_slug) for x in expected_list]
        
    if isinstance(actual_routing, str):
        actual_list = [actual_routing]
    else:
        actual_list = list(actual_routing)
        
    expected_set = {str(x).strip().lower() for x in expected_list}
    actual_set = {str(x).strip().lower() for x in actual_list}
    return expected_set.issubset(actual_set)

def check_citation(actual_citations, expected_sources, company_slug=None):
    if not expected_sources:
        return True
        
    if isinstance(expected_sources, str):
        expected_list = [expected_sources]
    else:
        expected_list = list(expected_sources)
        
    if not actual_citations:
        return False
        
    def normalize(text):
        text = str(text).lower().replace(" ", "").replace("_", "").replace("-", "")
        for prefix in ["astral", "craftsman", "automation", "ltd", "concall", "_ltd_"]:
            text = text.replace(prefix, "")
        return text

    citation_strings = []
    for c in actual_citations:
        if isinstance(c, dict):
            fname = c.get("filename") or c.get("source_url") or c.get("source_uri") or ""
            col = c.get("collection") or ""
            citation_strings.append(normalize(fname))
            if col:
                citation_strings.append(normalize(col))
        else:
            citation_strings.append(normalize(c))
            
    citations_combined = " ".join(citation_strings)
    
    for expected in expected_list:
        expected_raw = str(expected).lower()
        expected_clean = Path(expected_raw).name
        
        if normalize(expected_clean) in citations_combined or normalize(expected_raw) in citations_combined:
            return True
            
    return False

def run_ragas_evaluation(results: list) -> dict:
    if not RAGAS_AVAILABLE:
        print("⚠️ RAGAS not installed or import failed. Skipping RAGAS evaluation.")
        return {"error": "RAGAS not available"}

    questions = []
    answers = []
    contexts = []
    ground_truths = []
    indices = []

    for idx, r in enumerate(results):
        # Extract actual chunks (either from actual_chunks list of string or from chunks list of dicts)
        chunks = r.get("actual_chunks") or []
        if not chunks:
            # Try to parse from 'chunks' list of dicts
            raw_chunks = r.get("chunks", [])
            chunks = [c.get("content", "") for c in raw_chunks if isinstance(c, dict) and "content" in c]
            
        actual_ans = r.get("answer") or r.get("actual_answer") or ""
        expected_ans = r.get("expected_answer") or ""
        question = r.get("question") or ""

        if not chunks or not actual_ans or not expected_ans:
            continue

        questions.append(question)
        answers.append(actual_ans)
        contexts.append([c for c in chunks if isinstance(c, str)])
        ground_truths.append(expected_ans)
        indices.append(idx)

    if not questions:
        return {"error": "No questions with valid chunks and answers for RAGAS evaluation"}

    print(f"\nRunning RAGAS evaluation on {len(questions)} questions...")

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
        # Use gpt-4o-mini if gpt-4.1-mini is not valid, but let's match score_eval.py's gpt-4.1-mini
        # Wait, let's look at what model score_eval.py used: "gpt-4.1-mini"
        # We will match score_eval.py exactly: gpt-4.1-mini.
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

        def _safe_nanmean(col_name):
            if col_name not in df.columns:
                return None
            val = np.nanmean(df[col_name])
            if np.isnan(val):
                return None
            return round(float(val), 4)

        # Store individual question scores back in results list
        for i, idx in enumerate(indices):
            results[idx]["ragas_scores"] = {
                "faithfulness": float(df.iloc[i]["faithfulness"]) if "faithfulness" in df.columns and not np.isnan(df.iloc[i]["faithfulness"]) else None,
                "answer_relevancy": float(df.iloc[i]["answer_relevancy"]) if "answer_relevancy" in df.columns and not np.isnan(df.iloc[i]["answer_relevancy"]) else None,
                "context_recall": float(df.iloc[i]["context_recall"]) if "context_recall" in df.columns and not np.isnan(df.iloc[i]["context_recall"]) else None,
                "context_precision": float(df.iloc[i]["context_precision"]) if "context_precision" in df.columns and not np.isnan(df.iloc[i]["context_precision"]) else None,
            }

        return {
            "questions_evaluated": len(questions),
            "faithfulness": _safe_nanmean("faithfulness"),
            "answer_relevancy": _safe_nanmean("answer_relevancy"),
            "context_recall": _safe_nanmean("context_recall"),
            "context_precision": _safe_nanmean("context_precision"),
            "individual_results": df.to_dict(orient="records")
        }

    except Exception as e:
        print(f"Error running RAGAS evaluation: {e}")
        return {"error": str(e)}

def score_file(results_file: Path, run_output_dir: Path, company: str, run_ragas: bool):
    if not results_file.exists():
        print(f"Error: Results file not found at {results_file}")
        return
        
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    results = data.get("results", [])
    if not results:
        print(f"No results found in {results_file}")
        return
        
    total_questions = len(results)
    routing_correct_count = 0
    citation_correct_count = 0
    
    section_stats = {}
    
    grading_lines = []
    grading_lines.append(f"Manual Grading File for {company.upper()} — Run: {data.get('run_name')}\n")
    grading_lines.append("=" * 80 + "\n\n")
    
    report_lines = []
    report_lines.append(f"FinBot Benchmark Report ({company.upper()})\n")
    report_lines.append(f"Run: {data.get('run_name')}\n")
    report_lines.append("=" * 80 + "\n\n")
    
    for i, r in enumerate(results, 1):
        q_id = r.get("id", f"Q{i}")
        section = r.get("section", "Unknown")
        question = r.get("question", "")
        expected_ans = r.get("expected_answer", "")
        actual_ans = r.get("answer", "")
        
        expected_rout = r.get("expected_routing", [])
        actual_rout = r.get("collections_searched", [])
        
        expected_src = r.get("expected_source", [])
        actual_cit = r.get("citations", [])
        
        # Scoring
        routing_correct = check_routing(actual_rout, expected_rout, company)
        citation_correct = check_citation(actual_cit, expected_src, company)
        
        if routing_correct:
            routing_correct_count += 1
        if citation_correct:
            citation_correct_count += 1
            
        # Section stats
        if section not in section_stats:
            section_stats[section] = {"total": 0, "routing_correct": 0, "citation_correct": 0}
        section_stats[section]["total"] += 1
        section_stats[section]["routing_correct"] += int(routing_correct)
        section_stats[section]["citation_correct"] += int(citation_correct)
        
        # Write to grading lines
        grading_lines.append(f"Question {i} (ID: {q_id}) [{section}]\n")
        grading_lines.append(f"Q: {question}\n")
        grading_lines.append(f"Expected Answer: {expected_ans}\n")
        grading_lines.append(f"Actual Answer:   {actual_ans}\n")
        grading_lines.append("-" * 80 + "\n\n")
        
        # Write to report lines
        report_lines.append(f"Q{i} (ID: {q_id}) [{section}]\n")
        report_lines.append(f"Question: {question}\n")
        report_lines.append(f"Routing:  {'✅ PASS' if routing_correct else '❌ FAIL'} (Expected: {expected_rout} | Got: {actual_rout})\n")
        report_lines.append(f"Citation: {'✅ PASS' if citation_correct else '❌ FAIL'} (Expected: {expected_src} | Got: {[c.get('filename') for c in actual_cit if isinstance(c, dict)]})\n")
        report_lines.append(f"Latency:  {r.get('latency_seconds', 0)}s\n")
        report_lines.append("-" * 80 + "\n\n")
        
    # Compute metrics
    routing_acc = (routing_correct_count / total_questions) * 100 if total_questions else 0
    citation_acc = (citation_correct_count / total_questions) * 100 if total_questions else 0
    
    summary_text = []
    summary_text.append("=" * 60)
    summary_text.append(f"  BENCHMARK SUMMARY - {company.upper()}")
    summary_text.append("=" * 60)
    summary_text.append(f"Total Questions:          {total_questions}")
    summary_text.append(f"Total Routing Accuracy:   {routing_correct_count}/{total_questions} ({routing_acc:.2f}%)")
    summary_text.append(f"Total Citation Accuracy:  {citation_correct_count}/{total_questions} ({citation_acc:.2f}%)")
    summary_text.append("\nPer-Section Breakdown:")
    
    for sect, stats in section_stats.items():
        sect_total = stats["total"]
        sect_rout = stats["routing_correct"]
        sect_cit = stats["citation_correct"]
        r_pct = (sect_rout / sect_total) * 100 if sect_total else 0
        c_pct = (sect_cit / sect_total) * 100 if sect_total else 0
        summary_text.append(f"  {sect:<15} | Routing: {sect_rout}/{sect_total} ({r_pct:.1f}%) | Citations: {sect_cit}/{sect_total} ({c_pct:.1f}%)")
    summary_text.append("=" * 60 + "\n")
    
    # Run RAGAS if requested
    ragas_summary = {}
    if run_ragas:
        ragas_summary = run_ragas_evaluation(results)
        if "error" not in ragas_summary:
            summary_text.append("=" * 60)
            summary_text.append("  RAGAS OVERALL AVERAGES")
            summary_text.append("=" * 60)
            summary_text.append(f"Faithfulness:        {ragas_summary.get('faithfulness')}")
            summary_text.append(f"Answer Relevancy:    {ragas_summary.get('answer_relevancy')}")
            summary_text.append(f"Context Recall:      {ragas_summary.get('context_recall')}")
            summary_text.append(f"Context Precision:   {ragas_summary.get('context_precision')}")
            summary_text.append("=" * 60)
            
            # Print per-question RAGAS scores to score txt file
            report_lines.append("\n" + "=" * 60 + "\n")
            report_lines.append("  INDIVIDUAL RAGAS SCORES\n")
            report_lines.append("=" * 60 + "\n\n")
            for idx, r in enumerate(results):
                if "ragas_scores" in r:
                    report_lines.append(f"Q{idx+1} (ID: {r.get('id')}) [{r.get('section')}]\n")
                    report_lines.append(f"  Faithfulness:      {r['ragas_scores'].get('faithfulness')}\n")
                    report_lines.append(f"  Answer Relevancy:  {r['ragas_scores'].get('answer_relevancy')}\n")
                    report_lines.append(f"  Context Recall:    {r['ragas_scores'].get('context_recall')}\n")
                    report_lines.append(f"  Context Precision: {r['ragas_scores'].get('context_precision')}\n")
                    report_lines.append("-" * 30 + "\n")
                    
            # Compute Section-level RAGAS averages
            section_ragas = {}
            for r in results:
                sect = r.get("section", "Unknown")
                scores = r.get("ragas_scores")
                if not scores:
                    continue
                if sect not in section_ragas:
                    section_ragas[sect] = {
                        "faithfulness": [],
                        "answer_relevancy": [],
                        "context_recall": [],
                        "context_precision": []
                    }
                for k, v in scores.items():
                    if v is not None:
                        section_ragas[sect][k].append(v)
            
            summary_text.append("\nPer-Section RAGAS Breakdown:")
            for sect, metrics_dict in section_ragas.items():
                summary_text.append(f"  {sect:<15}:")
                for metric_name, val_list in metrics_dict.items():
                    avg_val = round(sum(val_list) / len(val_list), 4) if val_list else "N/A"
                    summary_text.append(f"    {metric_name:<18}: {avg_val}")
            summary_text.append("=" * 60 + "\n")
            
            # Save RAGAS results JSON
            ragas_output_file = run_output_dir / f"{company}_ragas_scores.json"
            with open(ragas_output_file, "w", encoding="utf-8") as f:
                json.dump({
                    "company": company,
                    "run_name": data.get("run_name"),
                    "averages": {
                        "faithfulness": ragas_summary.get('faithfulness'),
                        "answer_relevancy": ragas_summary.get('answer_relevancy'),
                        "context_recall": ragas_summary.get('context_recall'),
                        "context_precision": ragas_summary.get('context_precision'),
                    },
                    "results": results
                }, f, indent=2, ensure_ascii=False)
            print(f"Saved RAGAS JSON to:          {ragas_output_file}")
            
    # Print summary to console
    print("\n".join(summary_text))
    
    # Save grading file
    grading_file = run_output_dir / f"{company}_grading.txt"
    with open(grading_file, "w", encoding="utf-8") as f:
        f.writelines(grading_lines)
        
    # Save score report
    score_file_path = run_output_dir / f"{company}_scores.txt"
    with open(score_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_text) + "\n\n")
        f.writelines(report_lines)
        
    print(f"Saved manual grading view to: {grading_file}")
    print(f"Saved full score report to:    {score_file_path}\n")

def main():
    args = parse_args()
    
    base_dir = Path(__file__).parent
    run_dir = base_dir / "runs" / args.run_name
    
    if not run_dir.exists():
        print(f"Error: Run directory does not exist at {run_dir}")
        sys.exit(1)
        
    if args.company:
        target_file = run_dir / f"{args.company}_results.json"
        if not target_file.exists():
            print(f"Error: File for company '{args.company}' not found at {target_file}")
            sys.exit(1)
        results_files = [target_file]
    else:
        results_files = list(run_dir.glob("*_results.json"))
    
    if not results_files:
        print(f"Error: No *_results.json files found in {run_dir}")
        sys.exit(1)
        
    for rf in results_files:
        company = rf.stem.replace("_results", "")
        print(f"Scoring results for company: {company}...")
        score_file(rf, run_dir, company, args.ragas)

if __name__ == "__main__":
    main()
