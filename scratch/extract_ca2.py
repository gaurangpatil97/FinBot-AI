import re
import json

def parse_dirty_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # The files probably contain multiple JSON objects separated by newlines or just concatenated
    # Let's find all occurrences of '"id": "CA'
    starts = [m.start() for m in re.finditer(r'\{\s*"id":\s*"CA[1-5]"', content)]
    for start in starts:
        # find matching brace
        brace_count = 0
        end = -1
        for i in range(start, len(content)):
            if content[i] == '{': brace_count += 1
            elif content[i] == '}': brace_count -= 1
            if brace_count == 0:
                end = i + 1
                break
        if end != -1:
            obj_str = content[start:end]
            try:
                obj = json.loads(obj_str)
                print(f"--- {filepath} {obj.get('id')} ---")
                print(f"Q: {obj.get('question')}")
                print(f"Expected: {obj.get('expected_answer')}")
                print(f"Actual: {obj.get('actual_answer')}")
                
                context_files = [c.get('source') for c in obj.get('context', [])]
                print(f"Context sources: {context_files}")
                print()
            except Exception as e:
                print('Error parsing object', e)
parse_dirty_json('astral100test.json')
parse_dirty_json('craftsman100test.json')
