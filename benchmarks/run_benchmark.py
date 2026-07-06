import json
import argparse
import time
import requests
import sys
from pathlib import Path

# Force UTF-8 stdout for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api/v1/query"

def parse_args():
    parser = argparse.ArgumentParser(description="Run FinBot benchmarks")
    parser.add_argument(
        "--company",
        required=True,
        choices=["astral_ltd", "craftsman_automation_ltd"],
        help="Company slug to test (astral_ltd or craftsman_automation_ltd)"
    )
    parser.add_argument(
        "--run-name",
        required=True,
        help="Name of the run, e.g. run_001"
    )
    return parser.parse_args()

def fire_question(question: str, company_slug: str) -> dict:
    payload = {
        "question": question,
        "company_slug": company_slug,
        "year": None
    }
    start = time.time()
    try:
        # 120 second timeout matches craftsman evaluation script
        resp = requests.post(API_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        latency = round(time.time() - start, 2)
        data["latency_seconds"] = latency
        return data
    except Exception as e:
        latency = round(time.time() - start, 2)
        print(f"Error firing question: {e}")
        return {
            "answer": f"ERROR: {e}",
            "citations": [],
            "collections_searched": [],
            "routing_debug": {},
            "chunks": [],
            "latency_seconds": latency
        }

def main():
    args = parse_args()
    
    # Define directories
    base_dir = Path(__file__).parent
    questions_dir = base_dir / "questions"
    runs_dir = base_dir / "runs"
    
    # Determine the company specific questions file
    if args.company == "astral_ltd":
        specific_file = questions_dir / "astral_specific_60.json"
    else:
        specific_file = questions_dir / "craftsman_specific_60.json"
        
    agnostic_file = questions_dir / "agnostic_40.json"
    
    # Load and merge files
    if not agnostic_file.exists():
        print(f"Error: Agnostic questions file not found at {agnostic_file}")
        sys.exit(1)
        
    if not specific_file.exists():
        print(f"Error: Company-specific questions file not found at {specific_file}")
        sys.exit(1)
        
    with open(agnostic_file, "r", encoding="utf-8") as f:
        agnostic_questions = json.load(f)
        
    with open(specific_file, "r", encoding="utf-8") as f:
        specific_questions = json.load(f)
        
    # Merge questions
    all_questions = agnostic_questions + specific_questions
    
    print(f"Loaded {len(agnostic_questions)} agnostic questions and {len(specific_questions)} specific questions.")
    print(f"Total merged questions: {len(all_questions)}")
    print(f"Running benchmarks for {args.company} with run name {args.run_name}...\n")
    
    results = []
    
    for i, q in enumerate(all_questions, 1):
        question_text = q["question"]
        print(f"Question {i}/{len(all_questions)}...", end="", flush=True)
        
        # Fire query
        response_data = fire_question(question_text, args.company)
        
        # Merge response keys into the question item
        result_item = q.copy()
        result_item["answer"] = response_data.get("answer", "")
        result_item["citations"] = response_data.get("citations", [])
        result_item["routing_debug"] = response_data.get("routing_debug", {})
        result_item["chunks"] = response_data.get("chunks", [])
        result_item["collections_searched"] = response_data.get("collections_searched", [])
        result_item["latency_seconds"] = response_data.get("latency_seconds", 0)
        
        results.append(result_item)
        
        print(f" done ({response_data.get('latency_seconds', 0.0)}s)")
        
    # Save the output file
    run_output_dir = runs_dir / args.run_name
    run_output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = run_output_dir / f"{args.company}_results.json"
    
    output_data = {
        "company": args.company,
        "run_name": args.run_name,
        "results": results
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved {len(results)} results to {output_file}")

if __name__ == "__main__":
    main()
