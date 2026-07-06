import json
import requests
import sys
import re
import time

sys.stdout.reconfigure(encoding='utf-8')

def get_q(file, qid):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    matches = re.finditer(r'"id"\s*:\s*"([^"]+)"', content)
    for m in matches:
        if m.group(1) == qid:
            start = m.end()
            q_match = re.search(r'"question"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', content[start:])
            if q_match:
                return q_match.group(1).replace('\\"', '"')
    return None

def find_q_anywhere(qid, files):
    for f in files:
        q = get_q(f, qid)
        if q: return q
    return f"UNKNOWN QUESTION {qid}"

astral_files = ['D:/FinBot/benchmarks/questions/astral_100.json', 'D:/FinBot/benchmarks/questions/astral_specific_60.json', 'D:/FinBot/benchmarks/questions/agnostic_40.json']

queries = [
    ('astral_ltd', 'CP4', find_q_anywhere('CP4', astral_files)),
    ('astral_ltd', 'CP6', find_q_anywhere('CP6', astral_files)),
    ('astral_ltd', 'CP7', find_q_anywhere('CP7', astral_files))
]

for company, qid, q in queries:
    print(f"\n=============================================")
    print(f"--- {company} {qid} ---")
    print(f"Question: {q}")
    try:
        res = requests.post(
            f'http://localhost:8000/api/v1/query',
            json={'question': q, 'company_slug': company}
        )
        if res.status_code == 200:
            data = res.json()
            print(f"Answer:\n{data.get('answer')}")
            print("\nSources:")
            for s in data.get('citations', []):
                print(f"  - {s.get('filename')} (Page {s.get('page')})")
        else:
            print(f"Error: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Request failed: {e}")
    time.sleep(1)
