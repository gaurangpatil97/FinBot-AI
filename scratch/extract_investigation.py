import json

astral_file = 'benchmarks/runs/run_001/astral_ltd_results.json'
craftsman_file = 'benchmarks/runs/run_001/craftsman_automation_ltd_results.json'

def investigate(file_path, q_ids, out_file):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)['results']
        for d in data:
            if d.get('id') in q_ids:
                out_file.write(f"========== {d.get('id')} ==========\n")
                out_file.write(f"ACTUAL SOURCES (citations):\n")
                for i, src in enumerate(d.get('citations', [])):
                    out_file.write(f"  {i+1}. {src}\n")
                out_file.write(f"\nEXPECTED SOURCES:\n")
                for i, src in enumerate(d.get('expected_source', [])):
                    out_file.write(f"  {i+1}. {src}\n")
                out_file.write(f"\nACTUAL ANSWER:\n{d.get('answer', '')}\n")
                out_file.write(f"\nEXPECTED ANSWER:\n{d.get('expected_answer', '')}\n")
                out_file.write("==================================\n\n")

with open('scratch/investigation_output.txt', 'w', encoding='utf-8') as out_f:
    out_f.write("--- ASTRAL ---\n")
    investigate(astral_file, ['P4', 'P8', 'P1', 'P9', 'CP1', 'CP4', 'CP7', 'P3', 'P7', 'P10'], out_f)
    out_f.write("\n--- CRAFTSMAN ---\n")
    investigate(craftsman_file, ['P4', 'P8', 'CP2', 'CP3', 'P10', 'P9', 'P3', 'P7'], out_f)
