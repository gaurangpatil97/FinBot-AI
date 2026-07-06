import json

all_ids = [f'P{i}' for i in range(1, 11)] + [f'CP{i}' for i in range(1, 11)]

for comp, ids in [('astral_ltd', all_ids), ('craftsman_automation_ltd', all_ids)]:
    with open(f'd:/FinBot/benchmarks/runs/run_001/{comp}_results.json', encoding='utf-8') as f:
        data = json.load(f)['results']
        with open('final_output_40.txt', 'a', encoding='utf-8') as out:
            for q in data:
                if q['id'] in ids:
                    out.write(f'=== [{comp}] [{q["id"]}] ===\n')
                    out.write(f'QUESTION: {q.get("question", "")}\n')
                    out.write(f'EXPECTED: {q.get("expected_answer", "")}\n')
                    out.write(f'NEW ACTUAL: {q.get("answer", "")}\n')
                    citations = ", ".join([c.get("filename", "") for c in q.get("citations", [])])
                    out.write(f'FILENAME CITED: {citations}\n\n')
