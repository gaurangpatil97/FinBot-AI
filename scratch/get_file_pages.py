import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

astral_qs = ['P3', 'P4', 'P7', 'P8', 'P10', 'CP4', 'CP6', 'CP7']
craftsman_qs = ['P3', 'P4', 'P7', 'P8', 'P10', 'CP3', 'CP4']

def extract_file_page_pairs(file_path, q_ids):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        pairs = set()
        
        for q_id in q_ids:
            q = next((r for r in data.get('results', []) if r.get('id') == q_id), None)
            if q:
                # Use citations array to get exact filename and page
                citations = q.get('citations', [])
                for c in citations:
                    filename = c.get('filename')
                    page = c.get('page')
                    if filename and isinstance(page, int):
                        # Filter out excel files, we only care about PDFs
                        if filename.endswith('.pdf'):
                            pairs.add((filename, page))
            else:
                print(f'{file_path.split("/")[-1]} {q_id}: Not found')
                
        return pairs
    except Exception as e:
        print(f'Error: {e}')
        return set()

astral_pairs = extract_file_page_pairs('benchmarks/runs/run_001/astral_ltd_results.json', astral_qs)
craftsman_pairs = extract_file_page_pairs('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', craftsman_qs)

print("--- Astral ---")
for filename, page in sorted(list(astral_pairs)):
    print(f"('{filename}', {page})")
    
print("--- Craftsman ---")
for filename, page in sorted(list(craftsman_pairs)):
    print(f"('{filename}', {page})")
