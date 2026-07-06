import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

files = [
    ('ASTRAL', r'D:\FinBot\benchmarks\runs\run_001\astral_ltd_results.json'),
    ('CRAFTSMAN', r'D:\FinBot\benchmarks\runs\run_001\craftsman_automation_ltd_results.json')
]

for company, path in files:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = data.get('results', []) if isinstance(data, dict) else data
        
        for r in results:
            qid = r.get('id', '')
            if 'CX' in qid:
                print(f'=== [{company}] [{qid}] ===')
                print(f"QUESTION: {r.get('question', '')}")
                
                expected_ans = r.get('expected_answer', r.get('ground_truth', ''))
                actual_ans = r.get('actual_answer', r.get('answer', ''))
                print(f"EXPECTED: {expected_ans}")
                print(f"ACTUAL: {actual_ans}")
                
                # Handling different possible keys for routing/sources
                expected_routing = r.get('expected_routing', '')
                actual_routing = r.get('actual_routing', '')
                
                print(f"EXPECTED ROUTING/SOURCES: {expected_routing}")
                print(f"ACTUAL ROUTING/SOURCES: {actual_routing}")
                print()
    except Exception as e:
        print(f"Error reading {path}: {e}")
