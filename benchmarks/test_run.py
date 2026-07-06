import json, requests

with open("benchmarks/questions/agnostic_40.json") as f:
    qs = json.load(f)

for q in qs[:3]:
    qid = q["id"]
    qtxt = q["question"][:50]
    print(f"Testing {qid}: {qtxt}...")
    r = requests.post("http://localhost:8000/api/v1/query", json={"question": q["question"], "company_slug": "astral_ltd", "year": None})
    print(f"  Status: {r.status_code}")
    print(f"  Answer: {r.json().get('answer', 'ERROR')[:100]}...")
    print()
