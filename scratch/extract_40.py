import json

def dump_questions(file_path, company, q_ids, out_file):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)['results']
        out_file.write(f"=== {company} ===\n")
        for d in data:
            if d['id'] in q_ids:
                out_file.write(f"ID: {d['id']}\n")
                out_file.write(f"EXPECTED: {d.get('expected_answer', '')}\n")
                out_file.write(f"ACTUAL: {d.get('answer', '')}\n")
                out_file.write(f"ROUTING: {d.get('routing_debug', {}).get('status', 'FAIL')} | CITATION: {d.get('citations', [])}\n")
                out_file.write("-" * 40 + "\n")

q_list = [f'P{i}' for i in range(1,11)] + [f'CP{i}' for i in range(1,11)]

with open('scratch/all_40_review.txt', 'w', encoding='utf-8') as out_f:
    dump_questions('benchmarks/runs/run_001/astral_ltd_results.json', 'ASTRAL', q_list, out_f)
    dump_questions('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', 'CRAFTSMAN', q_list, out_f)
