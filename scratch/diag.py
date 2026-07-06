import json
import re

def analyze_company(filename, company_name, out):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'results' in data:
            data = data['results']
            
        out.write(f"=== {company_name} ===\n")
        ci_qs = [q for q in data if q.get('section', '') == 'Images' or q.get('question_id', '').startswith('CI') or q.get('question_id', '').startswith('I')]
        
        for i, q in enumerate(ci_qs[:10], 1):
            qid = q.get('question_id', f'CI{i}')
            out.write(f"Question: {qid}\n")
            out.write(f"Q: {q.get('question')}\n")
            out.write(f"Expected: {q.get('expected_answer')}\n")
            
            ans = q.get('actual_answer', '')
            out.write(f"Actual: {ans[:200]}...\n")
            
            strict = q.get('strict_score', False)
            out.write(f"Strict Pass: {strict}\n")
            
            act_cit = q.get('actual_citations', [])
            act_str = [str(c.get('filename', '')) for c in act_cit if isinstance(c, dict)]
            out.write(f"Citations Cited: {', '.join(act_str)}\n")
            out.write("\n")
            
    except Exception as e:
        out.write(f"Error processing {filename}: {e}\n")

with open('scratch/diagnosis.txt', 'w', encoding='utf-8') as f:
    analyze_company('tests/results/eval_raw_results_astral_ltd_20260630_215531.json', 'Astral', f)
    analyze_company('tests/results/eval_final_craftsman_raw_results_20260703_021833.json', 'Craftsman', f)
