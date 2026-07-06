import json
import re
import sys
import openai
from config import get_settings

sys.stdout.reconfigure(encoding='utf-8')

settings = get_settings()
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def classify_time_series(question: str):
    q_lower = question.lower()
    
    # 2. Specific year patterns (Higher priority if explicitly comparing X to Y or listing specific years)
    years_found = re.findall(r"fy\s*\d{2,4}|20\d{2}", q_lower)
    # Remove duplicates
    years_found = list(set(years_found))
    if len(years_found) > 0 and len(years_found) <= 3:
        # Check if they are just recent years mentioned in passing or actual targets
        return "SPECIFIC_YEARS", f"regex_specific: {years_found}"
        
    # 1. Broad / Full time series keywords
    broad_patterns = [
        r"last \d+\s*(?:financial )?years",
        r"most recent \d+\s*(?:financial )?years",
        r"\d+-year",
        r"trend",
        r"over the years",
        r"historical",
        r"past \d+\s*(?:financial )?years",
        r"decade",
        r"how has .* changed over time",
        r"year-on-year trend",
        r"each of the most recent \d+ financial years"
    ]
    for p in broad_patterns:
        if re.search(p, q_lower):
            return "FULL_TIME_SERIES", f"regex_broad: {p}"
            
    # 3. LLM Fallback
    prompt = f"""You must classify the following financial question into one of two categories:
    FULL_TIME_SERIES: The question asks for data over all available years, a long trend (e.g. 5+ years), or historical analysis.
    SPECIFIC_YEARS: The question asks for data from specific, targeted years (e.g. a comparison between 2 specific years, or a single year's value).
    
    Question: {question}
    
    Return ONLY JSON: {{"category": "FULL_TIME_SERIES"}} or {{"category": "SPECIFIC_YEARS"}}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        cat = json.loads(response.choices[0].message.content.strip())["category"]
        return cat, "llm_fallback"
    except Exception as e:
        return "FULL_TIME_SERIES", "error_fallback"

def load_q(file, prefix=None):
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    res = {}
    for item in data:
        qid = item['id']
        res[qid] = item['question']
    return res

agnostic = load_q('benchmarks/questions/agnostic_40.json')
astral_ce = load_q('benchmarks/questions/astral_specific_60.json', 'CE')
craftsman_ce = load_q('benchmarks/questions/craftsman_specific_60.json', 'CE')

results = []

targets = [f'E{i}' for i in range(1,11)] + [f'R{i}' for i in range(1,11)]
for qid in targets:
    if qid in agnostic:
        c, r = classify_time_series(agnostic[qid])
        results.append((qid, c, "Broad", r, agnostic[qid]))

for qid in [f'CE{i}' for i in range(1,11)]:
    if qid in astral_ce:
        c, r = classify_time_series(astral_ce[qid])
        results.append((f'Astral {qid}', c, "Targeted", r, astral_ce[qid]))

for qid in [f'CE{i}' for i in range(1,11)]:
    if qid in craftsman_ce:
        c, r = classify_time_series(craftsman_ce[qid])
        results.append((f'Craftsman {qid}', c, "Targeted", r, craftsman_ce[qid]))

print(f"{'Question ID':<15} | {'Classification':<18} | {'Expected':<10} | {'Match':<5} | {'Reason':<40}")
print("-" * 100)
for qid, c, exp, r, q in results:
    match = "PASS" if (c == "FULL_TIME_SERIES" and exp == "Broad") or (c == "SPECIFIC_YEARS" and exp == "Targeted") else "FAIL"
    print(f"{qid:<15} | {c:<18} | {exp:<10} | {match:<5} | {r:<40}")
