import requests
import json

url = "http://localhost:8000/api/v1/query"

questions = [
    "What was the Net Profit reported by the company in FY26?",
    "Compute the Debt-to-Equity ratio for FY25 and FY26"
]

for q in questions:
    payload = {
        "question": q,
        "company_slug": "craftsman_automation_ltd"
    }
    try:
        resp = requests.post(url, json=payload, timeout=120)
        print(f"--- Question: {q} ---")
        print("STATUS:", resp.status_code)
        data = resp.json()
        print("ANSWER:", data.get("answer"))
        print("AGENT USED:", data.get("agent_used"))
        print("CHUNKS RETRIEVED:", len(data.get("chunks", [])))
        print("")
    except Exception as e:
        print("Error:", e)
