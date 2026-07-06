import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract(company, section):
    with open(f'D:/FinBot/benchmarks/runs/run_003/{company}_results.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    qs = [q for q in d['results'] if q.get('section') == section]
    with open('D:/FinBot/scratch/current_eval.txt', 'w', encoding='utf-8') as out:
        for q in qs:
            out.write(f"ID: {q['id']}\n")
            out.write(f"Expected: {q['expected_answer']}\n")
            ans = q.get('answer') or q.get('actual_answer') or ''
            ans_short = ans.split('## Sources')[0].strip()
            out.write(f"Actual: {ans_short}\n\n")

if __name__ == '__main__':
    extract(sys.argv[1], sys.argv[2])
