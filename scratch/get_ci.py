import json

def process(filename, name, out):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'results' in data:
            data = data['results']
            
        out.write(f"=== {name} ===\n")
        found = False
        for q in data:
            if q.get('section', '') == 'Images' or q.get('question_id', '').startswith('I') or q.get('question_id', '').startswith('CI'):
                found = True
                out.write(f"ID: {q.get('question_id', 'N/A')}\n")
                out.write(f"Q: {q.get('question', 'N/A')}\n")
                out.write(f"Expected: {q.get('expected_answer', 'N/A')}\n")
                out.write(f"Actual: {q.get('actual_answer', 'N/A')}\n")
                out.write(f"Strict Score: {q.get('strict_score', 'N/A')}\n")
                
                exp_cit = q.get('expected_citations', [])
                act_cit = q.get('actual_citations', [])
                act_str = [str(c.get('filename', '')) + " " + str(c.get('page', '')) if isinstance(c, dict) else str(c) for c in act_cit]
                
                out.write(f"Expected Cit: {exp_cit}\n")
                out.write(f"Actual Cit: {act_str}\n")
                out.write('-'*40 + '\n')
        
        if not found:
            out.write("No Image questions found.\n")
    except Exception as e:
        out.write(f"Error reading {filename}: {e}\n")

with open('scratch/ci_results_utf8.txt', 'w', encoding='utf-8') as f:
    process('tests/results/eval_raw_results_20260703_090659.json', 'Astral', f)
    process('tests/results/eval_final_craftsman_raw_results_20260703_021833.json', 'Craftsman', f)
