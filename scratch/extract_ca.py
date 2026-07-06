import json
import re

def extract_ca(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The file might have multiple top-level arrays concatenated like ][ or ]\n[
    content = re.sub(r'\]\s*\[', '],[', content)
    if not content.startswith('['):
        content = '[' + content + ']'
        
    try:
        data = json.loads(content)
        flat = []
        for o in data:
            if isinstance(o, list):
                flat.extend(o)
            else:
                flat.append(o)
    except json.JSONDecodeError as e:
        print(f"Error parsing {filename}: {e}")
        # fallback: use regex to find JSON blocks
        return

    ca_items = [x for x in flat if isinstance(x, dict) and str(x.get('id', '')).startswith('CA')]
    for x in ca_items:
        print(f"--- {filename} {x.get('id')} ---")
        print(f"Q: {x.get('question')}")
        print(f"Expected: {x.get('expected_answer')}")
        print(f"Actual: {x.get('actual_answer')}")
        
        # We also need the grade information.
        # Check if grading info exists inside the object
        # If not, it might be in astral_grades.json / craftsman_grades.json
        print()

extract_ca('astral100test.json')
extract_ca('craftsman100test.json')
