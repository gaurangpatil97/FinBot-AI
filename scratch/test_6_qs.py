import requests
import json
import os
import sys

qs = [
    # Astral CI1
    {"q": "According to the Group Revenue Breakup chart in the FY22 annual report infographic, what percentage of the total revenue did the Pipes segment contribute?", "slug": "astral_ltd", "id": "Astral CI1"},
    
    # Craftsman CI1
    {"q": "In the About the company infographic page of the FY22 annual report, a donut chart shows the revenue split by business segment. What are the three business segments shown and their respective percentage contributions?", "slug": "craftsman_automation_ltd", "id": "Craftsman CI1"},
    
    # Craftsman CI3
    {"q": "In the KPI Position section bar charts of the FY22 annual report, what is the trend in the Debt/EBITDA ratio over the five-year period shown FY18 to FY22?", "slug": "craftsman_automation_ltd", "id": "Craftsman CI3"},
    
    # Craftsman CI7
    {"q": "In the Over the years financial performance multi-year bar chart section of the FY23 annual report, the Debt-equity Ratio chart shows values across FY19 to FY23. In which year did the ratio peak and what was the peak value?", "slug": "craftsman_automation_ltd", "id": "Craftsman CI7"},
    
    # Craftsman CI9
    {"q": "In the donut chart labelled Revenue by Geography Consolidated Basis in the FY24 annual report, what percentage of total consolidated revenue of ₹4,452 Crore is derived from domestic sales versus exports?", "slug": "craftsman_automation_ltd", "id": "Craftsman CI9"},
    
    # Craftsman CI10
    {"q": "In the five-year bar charts under Performance Consolidated Basis on the KPI page of the FY24 annual report, compare the trajectory of Net Profit versus EBITDA from FY20 to FY24. In which year did Net Profit grow proportionally fastest?", "slug": "craftsman_automation_ltd", "id": "Craftsman CI10"},
]

API_URL = "http://localhost:8000/api/v1/query"

for q in qs:
    print(f"\n[{q['id']}] {q['q']}")  # unchanged
    try:
        resp = requests.post(API_URL, json={"question": q['q'], "company_slug": q['slug']})
        if resp.status_code == 200:
            data = resp.json()
            ans = data.get('answer', '')
            cites = [c['filename'] for c in data.get('citations', [])]
            print(f"Answer: {ans[:200]}...")
            print(f"Citations: {cites}")
        else:
            print(f"Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Failed: {e}")
