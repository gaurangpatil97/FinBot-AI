import requests, json

API_URL = "http://localhost:8000/api/v1/query"
company = "craftsman_automation_ltd"

queries = [
    {
        "id": "CI10",  # Real CI10 (CAGR footnote)
        "question": "In the FY22 annual report, opening pages contain CAGR infographics showing growth from FY18 to FY22 across Revenue, EBIT, EBITDA, and PAT. The PAT CAGR of 49% is significantly higher than Revenue CAGR of 11%. What specific caveat is noted on the Revenue CAGR infographic that a CA must flag?",
    },
    {
        "id": "CI5",  # Net Profit vs EBITDA question (correct ID)
        "question": "In the five-year bar charts under Performance Consolidated Basis on the KPI page of the FY24 annual report, compare the trajectory of Net Profit versus EBITDA from FY20 to FY24. In which year did Net Profit grow proportionally fastest?",
    },
]

for q in queries:
    print(f"\n--- Running {q['id']} ---")
    try:
        resp = requests.post(API_URL, json={"question": q["question"], "company_slug": company})
        if resp.status_code == 200:
            data = resp.json()
            ans = data.get('answer', '')
            citations = [c.get('filename') for c in data.get('citations', [])]
            print(f"Answer: {ans[:500]}...")
            print(f"Citations: {citations}\n")
        else:
            print(f"Error {resp.status_code}: {resp.text}\n")
    except Exception as e:
        print(f"Failed: {e}\n")
