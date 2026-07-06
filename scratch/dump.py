import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

agnostic = json.load(open('benchmarks/questions/agnostic_40.json', encoding='utf-8'))
astral = json.load(open('benchmarks/questions/astral_specific_60.json', encoding='utf-8'))
craftsman = json.load(open('benchmarks/questions/craftsman_specific_60.json', encoding='utf-8'))

ast_res = json.load(open('benchmarks/runs/run_001/astral_ltd_results.json', encoding='utf-8'))['results']
craft_res = json.load(open('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', encoding='utf-8'))['results']

def get_exp(qid, company):
    for q in agnostic:
        if q['id'] == qid:
            return q['expected_answer']
    src = astral if company == 'astral_ltd' else craftsman
    for q in src:
        if q['id'] == qid:
            return q['expected_answer']
    return 'NOT FOUND'

with open('manual_grade_dump.md', 'w', encoding='utf-8') as f:
    for company, res in [('astral_ltd', ast_res), ('craftsman_automation_ltd', craft_res)]:
        f.write(f'# {company}\n')
        for x in res:
            qid = x['id']
            if qid.startswith('E') or qid.startswith('R') or qid.startswith('CE'):
                f.write(f'## {qid}\n')
                f.write(f'**EXPECTED:** {get_exp(qid, company)}\n\n')
                f.write(f'**ACTUAL:** {x["answer"]}\n\n')
                f.write('---\n')
