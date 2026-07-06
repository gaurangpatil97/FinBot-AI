import json
import argparse
import time
import requests
import sys
from pathlib import Path

# Add parent directory to path so we can import from score_benchmark
sys.path.append(str(Path(__file__).parent))
from score_benchmark import check_citation, check_routing

API_URL = "http://localhost:8000/api/v1/query"

def parse_args():
    parser = argparse.ArgumentParser(description="Re-run a subset of FinBot benchmarks")
    parser.add_argument("--company", required=True, choices=["astral_ltd", "craftsman_automation_ltd"])
    parser.add_argument("--run-name", required=True)
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--question-ids", help="Comma-separated question IDs (e.g. R1,CA1)")
    group.add_argument("--section", help="Section name (e.g. Ratio, Anomaly)")
    
    return parser.parse_args()

def fire_question(question: str, company_slug: str) -> dict:
    payload = {
        "question": question,
        "company_slug": company_slug,
        "year": None
    }
    start = time.time()
    try:
        resp = requests.post(API_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        data["latency_seconds"] = round(time.time() - start, 2)
        return data
    except Exception as e:
        print(f"Error firing question: {e}")
        return {
            "answer": f"ERROR: {e}",
            "citations": [],
            "collections_searched": [],
            "routing_debug": {},
            "chunks": [],
            "latency_seconds": round(time.time() - start, 2)
        }

def main():
    args = parse_args()
    
    run_dir = Path(__file__).parent / "runs" / args.run_name
    results_file = run_dir / f"{args.company}_results.json"
    
    if not results_file.exists():
        print(f"Error: Results file not found at {results_file}")
        sys.exit(1)
        
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    results = data.get("results", [])
    
    if args.question_ids:
        target_ids = [x.strip() for x in args.question_ids.split(",")]
        target_indices = [i for i, q in enumerate(results) if q.get("id") in target_ids]
    else:
        target_indices = [i for i, q in enumerate(results) if q.get("section") == args.section]
        
    if not target_indices:
        print("No questions found matching criteria.")
        sys.exit(0)
        
    print(f"Found {len(target_indices)} questions to re-run.")
    
    summary = []
    
    for idx in target_indices:
        q = results[idx]
        q_id = q.get("id")
        section = q.get("section")
        
        # Before scores
        old_rout = check_routing(q.get("collections_searched", []), q.get("expected_routing", []))
        old_cit = check_citation(q.get("citations", []), q.get("expected_source", []))
        
        print(f"\nRe-running [{section}] ID: {q_id}...")
        resp_data = fire_question(q.get("question"), args.company)
        
        # Update question data
        results[idx]["answer"] = resp_data.get("answer", "")
        results[idx]["citations"] = resp_data.get("citations", [])
        results[idx]["routing_debug"] = resp_data.get("routing_debug", {})
        results[idx]["chunks"] = resp_data.get("chunks", [])
        results[idx]["collections_searched"] = resp_data.get("collections_searched", [])
        results[idx]["latency_seconds"] = resp_data.get("latency_seconds", 0)
        
        # After scores
        new_rout = check_routing(results[idx].get("collections_searched", []), results[idx].get("expected_routing", []))
        new_cit = check_citation(results[idx].get("citations", []), results[idx].get("expected_source", []))
        
        print(f"  Routing:  {'PASS' if old_rout else 'FAIL'} -> {'PASS' if new_rout else 'FAIL'}")
        print(f"  Citation: {'PASS' if old_cit else 'FAIL'} -> {'PASS' if new_cit else 'FAIL'}")
        
        summary.append({
            "id": q_id,
            "old_rout": old_rout, "new_rout": new_rout,
            "old_cit": old_cit, "new_cit": new_cit
        })
        
    # Save back
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved updated results to {results_file.name}")
    print("\n--- RE-RUN SUMMARY ---")
    for s in summary:
        print(f"ID: {s['id']:<4} | Routing: {str(s['old_rout'])[0]}->{str(s['new_rout'])[0]} | Citation: {str(s['old_cit'])[0]}->{str(s['new_cit'])[0]}")

if __name__ == "__main__":
    main()
