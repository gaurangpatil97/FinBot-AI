import re

with open('d:\\FinBot\\astral100test.json', 'r', encoding='utf-8') as f:
    text = f.read()
ids = re.findall(r'"id"\s*:\s*"([^"]+)"', text)
print('Unique IDs in astral100test.json:', sorted(list(set(ids))))

with open('d:\\FinBot\\craftsman100test.json', 'r', encoding='utf-8') as f:
    text2 = f.read()
ids2 = re.findall(r'"id"\s*:\s*"([^"]+)"', text2)
print('Unique IDs in craftsman100test.json:', sorted(list(set(ids2))))
