import os
import sys
import json
import time
import requests
from pathlib import Path

# Force UTF-8 stdout for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path to import config
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from config import settings

API_URL = "http://127.0.0.1:8000/api/v1/query"

# Load source questions from the files
def get_source_questions(filepath):
    import ast
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    start_idx = content.find("QUESTIONS = [")
    if start_idx == -1:
        return {}
    brackets = 1
    end_idx = start_idx + len("QUESTIONS = [")
    while brackets > 0 and end_idx < len(content):
        if content[end_idx] == "[":
            brackets += 1
        elif content[end_idx] == "]":
            brackets -= 1
        end_idx += 1
    list_str = content[start_idx + len("QUESTIONS = ") : end_idx]
    questions = ast.literal_eval(list_str)
    return {q["id"]: q for q in questions}

craftsman_qs = get_source_questions("tests/questions/run_evalCRASFTSMAN_AUTOMATION.py")

QUESTIONS_TO_RUN = [
    {"id": 5, "company": "craftsman_automation_ltd", "bucket": "calculation", "q_bank": craftsman_qs},
    {"id": 8, "company": "craftsman_automation_ltd", "bucket": "calculation", "q_bank": craftsman_qs},
]

def llm_judge_grade(question, expected_answer, actual_answer):
    import openai
    prompt = f"You are an expert financial auditor grading a RAG model's answer.\n\nQuestion: {question}\nExpected (Ground Truth): {expected_answer}\nActual Answer: {actual_answer}\n\nDetermine if the actual answer is correct and complete relative to the expected answer. Return ONLY a JSON object: {{\"grade\": \"Pass\"}} or {{\"grade\": \"Fail\", \"reason\": \"why it failed\"}}"
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        return result.get("grade", "Fail"), result.get("reason", "")
    except Exception as e:
        print(f"Error grading answer with LLM: {e}")
        return "Fail", str(e)

def main():
    print(f"Running Q5 and Q8 only against {API_URL}...")
    results = []
    for item in QUESTIONS_TO_RUN:
        q_id = item["id"]
        company = item["company"]
        bucket = item["bucket"]
        q_bank = item["q_bank"]
        q_meta = q_bank[q_id]
        question_text = q_meta["question"]
        expected_answer = q_meta["expected_answer"]
        print(f"Running Q{q_id} ({company})...")
        start = time.time()
        try:
            resp = requests.post(API_URL, json={"question": question_text, "company_slug": company}, timeout=300)
            latency = time.time() - start
            if resp.status_code == 200:
                payload = resp.json()
                actual = payload.get("answer", "")
                grade, reason = llm_judge_grade(question_text, expected_answer, actual)
            else:
                actual = f"API Error: {resp.status_code} - {resp.text}"
                grade, reason = "Fail", "HTTP Error"
        except Exception as e:
            latency = time.time() - start
            actual = f"Exception: {e}"
            grade, reason = "Fail", "Timeout or network exception"
        results.append({"id": f"Q{q_id}", "grade": grade, "reason": reason, "latency": latency})
        print(f"Result: Q{q_id} => {grade} (latency {latency:.2f}s) Reason: {reason}")
    print("\nSummary:")
    for r in results:
        print(f"{r['id']}: {r['grade']} (latency {r['latency']:.2f}s) Reason: {r['reason']}")

if __name__ == "__main__":
    main()
