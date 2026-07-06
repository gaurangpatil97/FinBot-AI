import sys
import os
import json
import requests

questions = {
    "C1": "What are the key revenue drivers and priorities outlined by management for the coming year?",
    "C3": "What near-term risks or challenges did management highlight during the calls?",
    "C4": "What is management's volume and margin guidance for the core business divisions?",
    "C6": "What are the capital expenditure (capex) plans and guidance for the current and next fiscal year?",
    "C7": "What capacity additions or plant updates did management detail?",
    "C8": "What updates did management provide regarding new acquisitions, overseas offices, or capacity expansion?",
    "C9": "What EBITDA margin contractions or fluctuations did management report, and what were the reasons?"
}

company_slug = "craftsman_automation_ltd"

for q_id, q_text in questions.items():
    print("=" * 50)
    print(f"ID: {q_id}")
    print(f"Question: {q_text}")
    print(f"Expected Citation: ...")
    
    try:
        r = requests.post(
            'http://127.0.0.1:8000/api/v1/query',
            json={'question': q_text, 'company_slug': company_slug}
        )
        data = r.json()
        print("Actual Answer: \n> " + data.get('answer', '').replace('\n', '\n> '))
        print("\nFull Sources (Actual Citations):")
        for c in data.get('citations', []):
            print(f"  - File: {c.get('filename')}, Page/Sheet: {c.get('page')}")
    except Exception as e:
        print("Error:", e)
    print("")

