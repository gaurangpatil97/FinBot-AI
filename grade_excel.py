import json
import os
import openai
import re
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_old_astral():
    old = {}
    with open('C:/Users/gaura/.gemini/antigravity-ide/scratch/evaluation_draft.json', 'r', encoding='utf-8') as f:
        evals = json.load(f)
        for ev in evals:
            qid = ev['id']
            if qid.startswith('E') or qid.startswith('R') or qid.startswith('CE'):
                old[qid] = {
                    'strict': ev.get('strict') == 'Correct',
                    'lenient': ev.get('lenient') in ['Correct', 'Partially Correct']
                }
    return old

def extract_old_craftsman():
    old = {}
    with open('benchmarks/runs/run_001/craftsman_manual_grading_report.md', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('| E') or line.startswith('| R') or line.startswith('| CE'):
                parts = [x.strip() for x in line.split('|')]
                if len(parts) > 6:
                    qid = parts[1]
                    strict = parts[5] == 'Correct'
                    lenient = parts[6] in ['Correct', 'Partially Correct']
                    old[qid] = {'strict': strict, 'lenient': lenient}
    return old

def llm_grade(question, expected, actual):
    prompt = f"""You are a strict financial grader for an AI benchmark.
Question: {question}
Expected Answer: {expected}
Actual Answer: {actual}

Grade the actual answer against the expected answer on two metrics:
1. Strict (True/False): Does the actual answer contain the EXACT numbers, ratios, or financial figures required by the expected answer (within a reasonable ±2% rounding tolerance)? If a question asks for 5 years, all 5 years must be present and correct.
2. Lenient (True/False): Is the actual answer substantively correct or directionally accurate, even if slightly imprecise or missing some minor details? If it incorrectly says data is unavailable when expected has it, it is False.

Output ONLY JSON:
{{"strict": true, "lenient": true}}
"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print('EXC:', e)
        return {"strict": False, "lenient": False}

def run_grading():
    astral_old = extract_old_astral()
    craftsman_old = extract_old_craftsman()
    
    for company, old_grades, results_file in [("astral", astral_old, "benchmarks/runs/run_001/astral_ltd_results.json"), 
                                              ("craftsman", craftsman_old, "benchmarks/runs/run_001/craftsman_automation_ltd_results.json")]:
        print(f"\nGrading {company}...")
        with open(results_file, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
            
        r_map = {x['id']: x for x in new_data['results']}
        target_ids = [f"E{i}" for i in range(1, 11)] + [f"CE{i}" for i in range(1, 11)] + [f"R{i}" for i in range(1, 11)]
        
        results = {}
        
        for qid in target_ids:
            if qid not in r_map:
                continue
            q = r_map[qid]
            question = q["question"]
            expected = q["expected_answer"]
            new_ans = q.get("answer", "")
            
            new_grades = llm_grade(question, expected, new_ans)
            old = old_grades.get(qid, {'strict': False, 'lenient': False})
            
            results[qid] = {
                "old_strict": old['strict'],
                "new_strict": new_grades["strict"],
                "old_lenient": old['lenient'],
                "new_lenient": new_grades["lenient"]
            }
            s_ch = "T->T" if old['strict'] and new_grades['strict'] else ("F->F" if not old['strict'] and not new_grades['strict'] else ("F->T" if not old['strict'] and new_grades['strict'] else "T->F"))
            l_ch = "T->T" if old['lenient'] and new_grades['lenient'] else ("F->F" if not old['lenient'] and not new_grades['lenient'] else ("F->T" if not old['lenient'] and new_grades['lenient'] else "T->F"))
            print(f"[{qid}] Strict: {s_ch} | Lenient: {l_ch}")
            
        with open(f"{company}_grades.json", "w") as f:
            json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_grading()
