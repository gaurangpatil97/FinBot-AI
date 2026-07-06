import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('benchmarks/runs/run_001/astral_ltd_results.json', encoding='utf-8') as f:
    d1 = json.load(f)['results']
    
with open('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', encoding='utf-8') as f:
    d2 = json.load(f)['results']

def get_pages(res, qs):
    out = {}
    for r in res:
        if r['id'] in qs:
            src = r['answer'].split('## Sources')[-1]
            pages = re.findall(r'Page (\d+)', src)
            out[r['id']] = list(set(pages))
    return out

print('Astral:', get_pages(d1, ['P3','P7','P10']))
print('Craftsman:', get_pages(d2, ['P3','P7','P10','CP4']))
