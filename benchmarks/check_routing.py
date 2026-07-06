import json

for fname in ["benchmarks/questions/agnostic_40.json", "benchmarks/questions/astral_specific_60.json"]:
    with open(fname) as f:
        qs = json.load(f)
    for q in qs:
        for r in q.get("expected_routing", []):
            if "astral" in r and "_ltd_" not in r:
                print(f"BAD ROUTING in {q['id']}: {r}")
    print(f"{fname}: {len(qs)} questions checked")
