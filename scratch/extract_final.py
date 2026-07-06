import json

def print_q(company, path, qids):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for r in data.get('results', []):
        if r.get('id') in qids:
            print(f"=== {company} {r.get('id')} ===")
            print(f"QUESTION: {r.get('question')}")
            print(f"EXPECTED: {r.get('expected_answer', r.get('ground_truth'))}")
            print(f"ACTUAL: {r.get('actual_answer', r.get('answer'))}")
            print(f"EXPECTED ROUTING: {r.get('expected_routing')}")
            print(f"ACTUAL ROUTING: {r.get('collections_searched')}")
            print()

print_q('ASTRAL', r'D:\FinBot\benchmarks\runs\run_001\astral_ltd_results.json', ['CX8', 'CX11'])
print_q('CRAFTSMAN', r'D:\FinBot\benchmarks\runs\run_001\craftsman_automation_ltd_results.json', ['CX11', 'CX3'])
