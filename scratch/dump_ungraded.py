import json

astral_graded = ['P1', 'P3', 'P4', 'P7', 'P8', 'P9', 'P10', 'CP1', 'CP4', 'CP7']
craftsman_graded = ['P3', 'P4', 'P7', 'P8', 'P9', 'P10', 'CP2', 'CP3']

def dump_ungraded(file_path, company, graded_ids, out_file):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)['results']
        out_file.write(f"=== {company} ===\n")
        for d in data:
            if d['id'].startswith('P') or d['id'].startswith('CP'):
                if d['id'] not in graded_ids:
                    out_file.write(f"ID: {d['id']}\n")
                    out_file.write(f"EXP: {d.get('expected_answer', '')}\n")
                    out_file.write(f"ACT: {d.get('answer', '')[:500]}...\n")
                    out_file.write("-" * 40 + "\n")

with open('scratch/ungraded.txt', 'w', encoding='utf-8') as out_f:
    dump_ungraded('benchmarks/runs/run_001/astral_ltd_results.json', 'ASTRAL', astral_graded, out_f)
    dump_ungraded('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', 'CRAFTSMAN', craftsman_graded, out_f)
