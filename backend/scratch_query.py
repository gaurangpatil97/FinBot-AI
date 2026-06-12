import requests

url = "http://localhost:8000/api/v1/query"
payload = {
    "question": "What was the Net Profit reported by the company in FY26?",
    "company_slug": "craftsman_automation_ltd"
}
try:
    resp = requests.post(url, json=payload, timeout=60)
    print("STATUS:", resp.status_code)
    print("RESPONSE:", resp.json())
except Exception as e:
    print("Error:", e)
