import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

def check_sources(file, q_ids):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results_list = data.get('results', [])
        
        for res in results_list:
            q_id = res.get('id')
            if q_id in q_ids:
                citations = res.get('citations', [])
                # Extract page numbers that are integers
                pages = list(set([c.get('page') for c in citations if isinstance(c.get('page'), int)]))
                print(f'{file.split("/")[-1]} {q_id}: Pages {sorted(pages)}')
                
    except Exception as e:
        print(f'Error: {e}')

print("--- Astral ---")
check_sources('benchmarks/runs/run_001/astral_ltd_results.json', ['P3', 'P7', 'P10'])
print("--- Craftsman ---")
check_sources('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', ['P3', 'P7', 'P10', 'CP4'])
