import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

files = ['benchmarks/questions/astral_100.json', 'benchmarks/questions/astral_specific_60.json', 'benchmarks/questions/agnostic_40.json']

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                if item.get('id') == 'CP6':
                    print(f'File: {f}')
                    print(f"Question: {item.get('question')}")
                    print(f"Expected: {item.get('expected_answer')}")
                    print("="*40)
    except Exception as e:
        print(e)
