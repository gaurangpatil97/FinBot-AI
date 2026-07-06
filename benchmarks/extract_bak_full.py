import json

with open(r'd:\FinBot\benchmarks\runs\run_001\astral_ltd_results.json.bak', 'r', encoding='utf-8') as f:
    data = json.load(f)

results_list = data.get('results', data) if isinstance(data, dict) else data

with open('astral_bak_full.txt', 'w', encoding='utf-8') as out_f:
    for result in results_list:
        if not isinstance(result, dict): continue
        q_id = result.get('id')
        if q_id in [f'P{i}' for i in range(1, 11)] + [f'CP{i}' for i in range(1, 11)]:
            out_f.write(f"=== {q_id} ===\n")
            out_f.write("EXPECTED:\n" + result.get('expected_answer', '') + "\n")
            out_f.write("ACTUAL:\n" + result.get('answer', '') + '\n')
            out_f.write("="*40 + "\n")
