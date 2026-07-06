import json

with open(r'd:\FinBot\benchmarks\runs\run_001\astral_ltd_results.json.bak', 'r', encoding='utf-8') as f:
    data = json.load(f)

results_list = data.get('results', data) if isinstance(data, dict) else data

with open('full_out.txt', 'w', encoding='utf-8') as out_f:
    for result in results_list:
        if not isinstance(result, dict): continue
        q_id = result.get('id')
        if q_id in ['CP4', 'CP5', 'CP6', 'CP7', 'P5']:
            out_f.write(f"=== {q_id} ===\n")
            out_f.write(result.get('answer', '') + '\n')
