import json

def extract_ca_results(filepath, out_file):
    out_file.write(f"--- Extracting from {filepath} ---\n")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        out_file.write(f"Error loading {filepath}: {e}\n")
        return
        
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if 'results' in data:
            items = data['results']
        else:
            items = list(data.values())
            
    for item in items:
        if not isinstance(item, dict): continue
        q_id = str(item.get('id', ''))
        if q_id.startswith('CA'):
            out_file.write(f"ID: {q_id}\n")
            out_file.write(f"Question: {item.get('question')}\n")
            out_file.write(f"Expected Answer: {item.get('expected_answer')}\n")
            out_file.write(f"Actual Answer: {item.get('actual_answer')}\n")
            out_file.write(f"Grade strict: {item.get('routing_correct_strict', item.get('routing_strict', 'N/A'))}\n")
            out_file.write(f"Routing debug: {item.get('routing_debug')}\n")
            out_file.write(f"Routed sources: {item.get('routed_sources')}\n")
            out_file.write(f"Actual citations: {item.get('actual_citations')}\n")
            out_file.write(f"Grade actual metrics: {item.get('grade', {})}\n")
            out_file.write("-" * 40 + "\n")

with open('d:\\FinBot\\scratch\\ca_results_dump.txt', 'w', encoding='utf-8') as out_file:
    extract_ca_results('d:\\FinBot\\benchmarks\\runs\\run_001\\astral_ltd_results.json', out_file)
    extract_ca_results('d:\\FinBot\\benchmarks\\runs\\run_001\\craftsman_automation_ltd_results.json', out_file)
