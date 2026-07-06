import json, os, requests

def load_questions(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def img_questions(data):
    return [(q['id'], q['question'], q.get('expected_answer', ''))
            for q in data if q.get('section') == 'Images' and q['id'].startswith('CI')]

base = r'd:\FinBot\benchmarks\questions'
astral_path = os.path.join(base, 'astral_specific_60.json')
craft_path = os.path.join(base, 'craftsman_specific_60.json')
astral = load_questions(astral_path)
craft = load_questions(craft_path)

questions = []
for qid, txt, exp in img_questions(astral):
    questions.append(('astral_ltd', qid, txt, exp))
for qid, txt, exp in img_questions(craft):
    questions.append(('craftsman_automation_ltd', qid, txt, exp))

api = 'http://localhost:8000/api/v1/query'
results = []
for comp, qid, txt, expected in questions:
    try:
        r = requests.post(api, json={'question': txt, 'company_slug': comp}, timeout=30)
        answer = r.json().get('answer', '') if r.status_code == 200 else ''
    except Exception:
        answer = ''
    strict = answer.strip() == expected.strip()
    lenient = expected.strip().lower() in answer.strip().lower() if answer else False
    results.append((qid, comp, strict, lenient))

print('| ID | Company | Strict | Lenient |')
print('|----|---------|--------|---------|')
for qid, comp, strict, lenient in results:
    print(f'| {qid} | {comp} | {strict} | {lenient} |')

astral_strict = sum(1 for r in results if r[1]=='astral_ltd' and r[2])
astral_lenient = sum(1 for r in results if r[1]=='astral_ltd' and r[3])
craft_strict = sum(1 for r in results if r[1]=='craftsman_automation_ltd' and r[2])
craft_lenient = sum(1 for r in results if r[1]=='craftsman_automation_ltd' and r[3])
print(f'Astral: {astral_strict}/10 Strict, {astral_lenient}/10 Lenient')
print(f'Craftsman: {craft_strict}/10 Strict, {craft_lenient}/10 Lenient')
