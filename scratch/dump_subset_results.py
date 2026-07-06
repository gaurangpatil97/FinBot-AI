import json

with open('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', encoding='utf-8') as f:
    d = json.load(f)['results']

ids = ['C1','C3','C4','C6','C7','C8','C9']
res = [r for r in d if r['id'] in ids]

with open('scratch/dump.txt', 'w', encoding='utf-8') as out:
    for r in res:
        out.write(f"\n{'='*50}\n")
        out.write(f"ID: {r['id']}\n")
        out.write(f"Question: {r['question']}\n")
        out.write(f"Expected Source/Citation: {r.get('expected_source')}\n")
        out.write(f"Actual Answer: {r.get('answer')}\n")
        
        sources = r.get('citations', [])
        out.write(f"\nFull Sources (Actual Citations):\n")
        for s in sources:
            out.write(f"  - File: {s.get('filename')}, Page/Sheet: {s.get('page')}\n")
