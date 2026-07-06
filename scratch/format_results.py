import json

with open('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', encoding='utf-8') as f:
    d = json.load(f)['results']

qs = ['C1','C3','C4','C6','C7','C8','C9']

with open('scratch/test_results.txt', 'w', encoding='utf-8') as out:
    for item in d:
        q = item['id']
        if q in qs:
            out.write("=" * 50 + "\n")
            out.write(f"ID: {q}\n")
            out.write(f"Question: {item['question']}\n")
            out.write(f"Expected Citation: {item['expected_source']}\n")
            ans = item['answer'].replace('\n', '\n> ')
            out.write(f"Actual Answer: \n> {ans}\n\n")
            out.write("Full Sources (Actual Citations):\n")
            for c in item['citations']:
                out.write(f"  - File: {c.get('filename')}, Page/Sheet: {c.get('page')}\n")
            out.write("\n")
