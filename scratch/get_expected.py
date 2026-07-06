import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_expected(file, qid):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    matches = re.finditer(r'"id"\s*:\s*"([^"]+)"', content)
    for m in matches:
        if m.group(1) == qid:
            start = m.end()
            q_match = re.search(r'"expected_answer"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', content[start:])
            if q_match:
                return q_match.group(1).replace('\\"', '"').replace('\\n', '\n')
    return None

astral_files = ['benchmarks/questions/astral_100.json', 'benchmarks/questions/astral_specific_60.json', 'benchmarks/questions/agnostic_40.json']
craftsman_files = ['benchmarks/questions/craftsman_100.json', 'benchmarks/questions/craftsman_specific_60.json', 'benchmarks/questions/agnostic_40.json']

def find_anywhere(qid, files):
    for f in files:
        a = get_expected(f, qid)
        if a: return a
    return 'NOT FOUND'

print('Astral CP4 EXPECTED:')
print(find_anywhere('CP4', astral_files))
print('\nAstral P1 EXPECTED:')
print(find_anywhere('P1', astral_files))
print('\nAstral P9 EXPECTED:')
print(find_anywhere('P9', astral_files))
print('\nCraftsman CP3 EXPECTED:')
print(find_anywhere('CP3', craftsman_files))
print('\nCraftsman P9 EXPECTED:')
print(find_anywhere('P9', craftsman_files))
