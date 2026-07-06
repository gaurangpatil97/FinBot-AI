import json
import sys

out_path = r'D:\FinBot\scratch\cx_raw_data.md'

files = [
    ('ASTRAL', r'D:\FinBot\benchmarks\runs\run_001\astral_ltd_results.json'),
    ('CRAFTSMAN', r'D:\FinBot\benchmarks\runs\run_001\craftsman_automation_ltd_results.json')
]

with open(out_path, 'w', encoding='utf-8') as out:
    out.write('# Cross-Source (CX) Questions Raw Dump\n\n')
    
    for company, path in files:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        results = data.get('results', [])
        
        for r in results:
            qid = r.get('id', '')
            if 'CX' in qid:
                out.write(f'### === [{company}] [{qid}] ===\n')
                out.write(f'**QUESTION:** {r.get("question", "")}\n\n')
                
                expected_ans = r.get('expected_answer', r.get('ground_truth', ''))
                actual_ans = r.get('actual_answer', r.get('answer', ''))
                
                out.write(f'**EXPECTED:** {expected_ans}\n\n')
                out.write(f'**ACTUAL:** {actual_ans}\n\n')
                
                out.write(f'**EXPECTED ROUTING:** {r.get("expected_routing", [])}\n\n')
                out.write(f'**ACTUAL ROUTING:** {r.get("collections_searched", [])}\n\n')
                out.write('---\n\n')
