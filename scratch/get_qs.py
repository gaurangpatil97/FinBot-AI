import json

def get_q(file, qid):
    with open(file, 'r', encoding='utf-8') as f:
        # Load as a list of dicts. If there's an error, maybe it's just a syntax error in the file, let's fix it by parsing properly.
        content = f.read()
    
    # Simple search
    import re
    matches = re.finditer(r'"id"\s*:\s*"([^"]+)"', content)
    for m in matches:
        if m.group(1) == qid:
            # find question after this
            start = m.end()
            q_match = re.search(r'"question"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', content[start:])
            if q_match:
                return q_match.group(1)
    return None

print('Astral CP4:', get_q('astral100test.json', 'CP4'))
print('Astral P1:', get_q('astral100test.json', 'P1'))
print('Astral P9:', get_q('astral100test.json', 'P9'))
print('Craftsman CP3:', get_q('craftsman100test.json', 'CP3'))
print('Craftsman P9:', get_q('craftsman100test.json', 'P9'))
