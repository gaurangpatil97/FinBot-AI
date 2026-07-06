import json
import os

bak_file = r'd:\FinBot\benchmarks\runs\run_001\astral_ltd_results.json.bak'

if not os.path.exists(bak_file):
    print("Bak file not found.")
else:
    with open(bak_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    with open('extracted.txt', 'w', encoding='utf-8') as out_f:
        out_f.write("Pre-fix answers from .bak for Astral PDF:\n")
        results_list = data.get('results', data) if isinstance(data, dict) else data
        for result in results_list:
            if not isinstance(result, dict):
                continue
            q_id = result.get('id')
            if q_id in [f'P{i}' for i in range(1, 11)] + [f'CP{i}' for i in range(1, 11)]:
                answer = result.get('answer', '')
                out_f.write(f"=== {q_id} ===\n")
                out_f.write(answer[:200].replace('\n', ' ') + "\n...\n")
