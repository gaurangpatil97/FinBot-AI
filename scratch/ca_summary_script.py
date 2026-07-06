import json

def print_summary(company, filepath, out):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('results', []) if isinstance(data, dict) else data
    out.write(f'# {company} Anomaly Results\n\n')
    for item in items:
        if str(item.get('id', '')).startswith('CA'):
            out.write(f'## {item.get("id")}\n')
            out.write(f'**Question:** {item.get("question")}\n\n')
            out.write(f'**Expected:** {item.get("expected_answer")}\n\n')
            out.write(f'**Actual:** {item.get("actual_answer", item.get("answer", "None"))}\n\n')
            strict = item.get('routing_correct_strict', item.get('routing_strict', None))
            out.write(f'**Routing Strict:** {strict}\n')
            out.write(f'**Routed Sources:** {item.get("routed_sources")}\n')
            citations = [c.get("collection") for c in item.get("citations", [])]
            out.write(f'**Actual Citations:** {citations}\n\n')

with open('d:\\FinBot\\scratch\\ca_summary.md', 'w', encoding='utf-8') as out:
    print_summary('Astral', 'd:\\FinBot\\benchmarks\\runs\\run_001\\astral_ltd_results.json', out)
    print_summary('Craftsman', 'd:\\FinBot\\benchmarks\\runs\\run_001\\craftsman_automation_ltd_results.json', out)
