import json
d = json.load(open('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', encoding='utf-8'))['results']
qs = ['C1','C3','C4','C6','C7','C8','C9']
with open('scratch/expected_answers.txt', 'w', encoding='utf-8') as f:
    for item in d:
        if item['id'] in qs:
            f.write(f"\nID: {item['id']}\nExpected Citation: {item['expected_source']}\nExpected Answer: {item['expected_answer']}\n")
