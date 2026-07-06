import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

for file_path in ['benchmarks/runs/run_001/astral_ltd_results.json', 'benchmarks/runs/run_001/craftsman_automation_ltd_results.json']:
    print(f"\n==== {file_path} ====")
    with open(file_path, encoding='utf-8') as f:
        data = json.load(f)
    
    results = data.get('results', [])
    for q in results:
        if q['id'] in ('R1', 'R2', 'R3'):
            print(f"[{q['id']}]")
            print("Question:", q.get('question'))
            print("Expected:", q.get('expected_answer'))
            print("Current Answer:\n", q.get('answer', ''))
            print("-" * 40)
