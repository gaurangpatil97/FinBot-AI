import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
ast_res = json.load(open('benchmarks/runs/run_001/astral_ltd_results.json', encoding='utf-8'))['results']
craft_res = json.load(open('benchmarks/runs/run_001/craftsman_automation_ltd_results.json', encoding='utf-8'))['results']

agnostic = {q['id']: q['expected_answer'] for q in json.load(open('benchmarks/questions/agnostic_40.json', encoding='utf-8'))}
astral_q = {q['id']: q['expected_answer'] for q in json.load(open('benchmarks/questions/astral_specific_60.json', encoding='utf-8'))}
craft_q = {q['id']: q['expected_answer'] for q in json.load(open('benchmarks/questions/craftsman_specific_60.json', encoding='utf-8'))}

def get_numbers(text):
    text = text.replace(',', '')
    matches = re.findall(r'-?\d+\.\d+|-?\d+', text)
    nums = []
    for m in matches:
        try:
            val = float(m)
            if 1 <= val <= 3000 or 1990 <= val <= 2030:
                # ignore small numbers and years
                if 1990 <= val <= 2030:
                    continue
            nums.append(val)
        except:
            pass
    return nums

def grade(actual, expected):
    exp_nums = get_numbers(expected)
    act_summary = actual.split('##')[1] if '##' in actual else actual
    act_nums = get_numbers(act_summary)
    
    if not exp_nums: return 'T', 'T'
    
    strict = True
    for e in exp_nums:
        found = False
        for a in act_nums:
            if abs(a - e) <= max(0.02 * abs(e), 0.05):
                found = True
                break
        if not found:
            strict = False
            break
    return 'T' if strict else 'F', 'T' if strict else 'F'

def print_grades(company, res, qs):
    print(f'\\n--- {company} ---')
    strict_e, lenient_e = 0, 0
    strict_r, lenient_r = 0, 0
    strict_ce, lenient_ce = 0, 0
    
    for x in res:
        qid = x['id']
        if not (qid.startswith('E') or qid.startswith('R') or qid.startswith('CE')): continue
        expected = agnostic.get(qid, qs.get(qid, ''))
        s, l = grade(x['answer'], expected)
        
        # Override for CE questions which may not match expected numbers precisely due to wording
        
        if 'E' in qid and 'CE' not in qid:
            strict_e += 1 if s=='T' else 0
            lenient_e += 1 if l=='T' else 0
        elif 'R' in qid:
            strict_r += 1 if s=='T' else 0
            lenient_r += 1 if l=='T' else 0
        elif 'CE' in qid:
            strict_ce += 1 if s=='T' else 0
            lenient_ce += 1 if l=='T' else 0
            
        print(f'{qid:4} | {s} | {l}')
        if s == 'F':
            print(f'   EXP: {expected[:150]}')
            ans = x['answer'].split("## Sources")[0]
            print(f'   ACT: {ans[:200]}')
            print()
            
    print(f'Excel Agnostic (10): {strict_e}/10 Strict, {lenient_e}/10 Lenient')
    print(f'Ratio Agnostic (10): {strict_r}/10 Strict, {lenient_r}/10 Lenient')
    print(f'Excel Specific (10): {strict_ce}/10 Strict, {lenient_ce}/10 Lenient')

print_grades('Astral', ast_res, astral_q)
print_grades('Craftsman', craft_res, craft_q)
