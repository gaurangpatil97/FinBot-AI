import json
import sys

def print_ci_qna(company, grades_file):
    try:
        with open(grades_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f'=== {company} ===')
        for item in data:
            if item.get('question_id', '').startswith('CI'):
                print(f"Q ID: {item.get('question_id')}")
                print(f"Q: {item.get('question')}")
                print(f"Expected: {item.get('expected_answer')}")
                print(f"Actual: {item.get('actual_answer')}")
                print(f"Grade: {item.get('strict_score')} Strict / {item.get('lenient_score')} Lenient")
                print(f"Actual Citations: {item.get('actual_citations')}")
                print(f"Expected Citations: {item.get('expected_citations')}")
                print('-'*40)
    except Exception as e:
        print(f'Error reading {grades_file}: {e}')

print_ci_qna('ASTRAL', 'astral_grades.json')
print_ci_qna('CRAFTSMAN', 'craftsman_grades.json')
