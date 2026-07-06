import json
import sys

def search_quarterly(filepath, company, out_file):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        items = data.get('results', []) if isinstance(data, dict) else data
        for item in items:
            q = item.get('question', '')
            if 'quarter' in q.lower() or 'q1' in q.lower() or 'q2' in q.lower() or 'q3' in q.lower() or 'q4' in q.lower():
                out_file.write(f'{company} - ID: {item.get("id")}\n')
                out_file.write(f'Question: {q}\n')
                out_file.write(f'Routed Sources: {item.get("routing_debug", {}).get("source_types")}\n')
                out_file.write('-'*40 + '\n')
    except Exception as e:
        out_file.write(f'Error: {e}\n')

with open('d:\\FinBot\\scratch\\quarterly_out.txt', 'w', encoding='utf-8') as out_file:
    search_quarterly('d:\\FinBot\\benchmarks\\runs\\run_001\\craftsman_automation_ltd_results.json', 'Craftsman', out_file)
    search_quarterly('d:\\FinBot\\benchmarks\\runs\\run_001\\astral_ltd_results.json', 'Astral', out_file)
