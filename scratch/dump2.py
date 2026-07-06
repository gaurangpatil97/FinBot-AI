import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
ast_res = json.load(open('benchmarks/runs/run_001/astral_ltd_results.json', encoding='utf-8'))['results']
craft_res = json.load(open('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', encoding='utf-8'))['results']

agnostic = {q['id']: q['expected_answer'] for q in json.load(open('benchmarks/questions/agnostic_40.json', encoding='utf-8'))}
astral_q = {q['id']: q['expected_answer'] for q in json.load(open('benchmarks/questions/astral_specific_60.json', encoding='utf-8'))}
craft_q = {q['id']: q['expected_answer'] for q in json.load(open('benchmarks/questions/craftsman_specific_60.json', encoding='utf-8'))}

out_path = r"C:\Users\gaura\.gemini\antigravity-ide\brain\702f32f4-f5ea-48a3-9691-1aead4a4eaa7\scratch\manual_grades.md"
os.makedirs(os.path.dirname(out_path), exist_ok=True)

with open(out_path, 'w', encoding='utf-8') as f:
    for company, res, qs in [('Astral', ast_res, astral_q), ('Craftsman', craft_res, craft_q)]:
        f.write(f'# {company}\n')
        for x in res:
            qid = x['id']
            if not (qid.startswith('E') or qid.startswith('R') or qid.startswith('CE')): continue
            expected = agnostic.get(qid, qs.get(qid, ''))
            f.write(f'### {qid}\n')
            f.write(f'**EXP:** {expected}\n\n')
            ans = x['answer'].split("## Sources")[0].strip() if '## Sources' in x['answer'] else x['answer']
            f.write(f'**ACT:** {ans}\n\n')
            f.write('---\n')
