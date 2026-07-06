import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('benchmarks/runs/run_001/astral_ltd_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    p7 = next((r for r in data['results'] if r.get('id') == 'P7'), None)
    if p7 and p7.get('answer'):
        print('P7 Answer:', repr(p7.get('answer')[-500:]))
    
    p10 = next((r for r in data['results'] if r.get('id') == 'P10'), None)
    if p10 and p10.get('answer'):
        print('P10 Answer:', repr(p10.get('answer')[-500:]))
