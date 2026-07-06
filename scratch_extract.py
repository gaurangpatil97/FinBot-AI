import json
with open('d:/FinBot/benchmarks/runs/run_001/craftsman_automation_ltd_results.json', encoding='utf-8') as f:
    data = json.load(f)
for q in data['results']:
    if q['id'] in ['C1', 'C2', 'C3', 'C4', 'C6', 'C7', 'C8']:
        print(f"ID: {q['id']}")
        print(f"Question: {q['question']}")
        print(f"Expected Source: {q.get('expected_source')}")
        print(f"Actual Citation: {q.get('citations')}")
        sources = set([c.get('metadata', {}).get('filename') for c in q.get('chunks', []) if isinstance(c.get('metadata'), dict)])
        print(f"Full Sources Used: {list(sources)}")
        print('-'*40)
