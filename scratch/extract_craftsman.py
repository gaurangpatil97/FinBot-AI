import json
import sys

def run():
    try:
        with open('d:/FinBot/benchmarks/runs/run_001/craftsman_automation_ltd_results.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        items = data.get('results', []) if isinstance(data, dict) else data
        with open('d:/FinBot/scratch/craftsman_ca_dump.txt', 'w', encoding='utf-8') as out:
            for q in items:
                if q['id'] in ['CA1', 'CA2', 'CA3', 'CA4', 'CA5']:
                    out.write(f"--- {q['id']} ---\n")
                    out.write(f"Routing: {q.get('routing_debug', {}).get('source_types')}\n")
                    out.write(q['answer'] + "\n\n")
    except Exception as e:
        print("Error:", e)
run()
