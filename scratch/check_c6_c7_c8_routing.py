import json

with open('d:/FinBot/benchmarks/runs/run_001/craftsman_automation_ltd_results.json', encoding='utf-8') as f:
    data = json.load(f)
for r in data['results']:
    if r['id'] in ['C6', 'C7', 'C8']:
        print(f"ID: {r['id']} | Routed to: {r['collections_searched']}")
