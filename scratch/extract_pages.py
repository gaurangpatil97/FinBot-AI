import json
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

def extract_pages(file, q_ids):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for q_id in q_ids:
            q = next((r for r in data.get('results', []) if r.get('id') == q_id), None)
            if q and q.get('answer'):
                answer = q['answer']
                if '## Sources' in answer:
                    sources_str = answer.split('## Sources')[-1]
                    # Find all matches between `· Page(s)` and `·`
                    matches = re.findall(r'Page[s]?\s+([0-9,\-\s]+)·', sources_str)
                    pages = []
                    for m in matches:
                        # Extract digits
                        nums = re.findall(r'\d+', m)
                        pages.extend([int(n) for n in nums])
                    print(f'{file.split("/")[-1]} {q_id}: {list(set(pages))}')
                else:
                    print(f'{file.split("/")[-1]} {q_id}: No ## Sources found')
            else:
                print(f'{file.split("/")[-1]} {q_id}: Not found')
    except Exception as e:
        print(f'Error: {e}')

print("--- Astral ---")
extract_pages('benchmarks/runs/run_001/astral_ltd_results.json', ['P3', 'P7', 'P10'])
print("--- Craftsman ---")
extract_pages('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', ['P3', 'P7', 'P10', 'CP4'])
