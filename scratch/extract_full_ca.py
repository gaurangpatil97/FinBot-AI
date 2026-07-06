import json

def extract_full(filepath, out_file):
    out_file.write(f"=== {filepath} ===\n")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('results', []) if isinstance(data, dict) else data
    for item in items:
        q_id = str(item.get('id', ''))
        if q_id.startswith('CA'):
            out_file.write(json.dumps(item, indent=2) + "\n")
            out_file.write("-" * 50 + "\n")

with open('d:\\FinBot\\scratch\\full_ca_dump.txt', 'w', encoding='utf-8') as out_file:
    extract_full('d:\\FinBot\\benchmarks\\runs\\run_001\\astral_ltd_results.json', out_file)
    extract_full('d:\\FinBot\\benchmarks\\runs\\run_001\\craftsman_automation_ltd_results.json', out_file)
