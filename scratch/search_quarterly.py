import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

def search_quarterly(filepath, company):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        items = data.get('results', []) if isinstance(data, dict) else data
        for item in items:
            q = item.get('question', '')
            if 'quarter' in q.lower() or 'q1' in q.lower() or 'q2' in q.lower() or 'q3' in q.lower() or 'q4' in q.lower():
                print(f'{company} - ID: {item.get("id")}')
                print(f'Question: {q}')
                print(f'Routed Sources: {item.get("routing_debug", {}).get("source_types")}')
                print('-'*40)
    except Exception as e:
        print('Error:', e)

search_quarterly('d:\\FinBot\\benchmarks\\runs\\run_001\\craftsman_automation_ltd_results.json', 'Craftsman')
search_quarterly('d:\\FinBot\\benchmarks\\runs\\run_001\\astral_ltd_results.json', 'Astral')
