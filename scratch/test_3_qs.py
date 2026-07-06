import json
import requests
import sys
from pathlib import Path

API_URL = "http://localhost:8000/api/v1/query"

sys.path.insert(0, str(Path("tests/questions").resolve()))
from Astral_questions_run_eval import QUESTIONS as ASTRAL_ALL
from final_craftsman_automation_run_eval import QUESTIONS as CRAFTSMAN_ALL

def get_images_questions(full_list):
    return [q for q in full_list if q.get("section") == "Images"]

astral_qs = get_images_questions(ASTRAL_ALL)
craftsman_qs = get_images_questions(CRAFTSMAN_ALL)

# Target: Astral CI1, Craftsman CI1, Craftsman CI9
targets = [
    ("Astral Ltd", "astral_ltd", astral_qs[0], "CI1"),
    ("Craftsman Automation", "craftsman_automation_ltd", craftsman_qs[0], "CI1"),
    ("Craftsman Automation", "craftsman_automation_ltd", craftsman_qs[8], "CI9")
]

for company_name, slug, q, qid in targets:
    print(f"\n[{company_name}] {qid}: {q['question'][:80]}...")
    resp = requests.post(API_URL, json={"question": q["question"], "company_slug": slug})
    if resp.status_code == 200:
        data = resp.json()
        print("Answer:", data.get("answer", "")[:200].replace("\n", " ") + "...")
        cites = [c.get("filename") if isinstance(c, dict) else str(c) for c in data.get("citations", [])]
        print("Citations:", cites)
    else:
        print("Error:", resp.text)
