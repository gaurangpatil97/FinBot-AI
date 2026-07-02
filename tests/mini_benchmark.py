import os
import sys
import json
import time
import requests
from pathlib import Path

# Force UTF-8 stdout for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path to import config
backend_path = Path(__file__).resolve().parent.parent / "backend"
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
    list_str = content[start_idx + len("QUESTIONS = "):end_idx]
    questions = ast.literal_eval(list_str)
    return {q["id"]: q for q in questions}

astral_qs = get_source_questions("tests/questions/Astral_questions_run_eval.py")
craftsman_qs = get_source_questions("tests/questions/run_evalCRASFTSMAN_AUTOMATION.py")

# Selected questions metadata
QUESTIONS_TO_RUN = [
    # CRAFTSMAN FAILURES (synthesis/hallucination)
    {"id": 10, "company": "craftsman_automation_ltd", "bucket": "synthesis", "q_bank": craftsman_qs},
    {"id": 64, "company": "craftsman_automation_ltd", "bucket": "synthesis", "q_bank": craftsman_qs},
    {"id": 71, "company": "craftsman_automation_ltd", "bucket": "synthesis", "q_bank": craftsman_qs},
    {"id": 35, "company": "craftsman_automation_ltd", "bucket": "synthesis", "q_bank": craftsman_qs},

    # CRAFTSMAN FAILURES (calculation)
    {"id": 5, "company": "craftsman_automation_ltd", "bucket": "calculation", "q_bank": craftsman_qs},
    {"id": 8, "company": "craftsman_automation_ltd", "bucket": "calculation", "q_bank": craftsman_qs},
    {"id": 32, "company": "craftsman_automation_ltd", "bucket": "calculation", "q_bank": craftsman_qs},

    # ASTRAL FAILURES (calculation)
    {"id": 25, "company": "astral_ltd", "bucket": "calculation", "q_bank": astral_qs},
    {"id": 26, "company": "astral_ltd", "bucket": "calculation", "q_bank": astral_qs},

    # SENTINELS (previously correct)
    {"id": 30, "company": "craftsman_automation_ltd", "bucket": "sentinel", "q_bank": craftsman_qs}, # concall
    {"id": 42, "company": "astral_ltd", "bucket": "sentinel", "q_bank": astral_qs},                 # concall
    {"id": 43, "company": "craftsman_automation_ltd", "bucket": "sentinel", "q_bank": craftsman_qs}, # PDF financials (rating)
    {"id": 36, "company": "astral_ltd", "bucket": "sentinel", "q_bank": astral_qs},                 # PDF financials (risk)
    {"id": 7, "company": "craftsman_automation_ltd", "bucket": "sentinel", "q_bank": craftsman_qs},  # calculation (debtor days)
    {"id": 23, "company": "astral_ltd", "bucket": "sentinel", "q_bank": astral_qs},                 # calculation (debtor days)
    {"id": 1, "company": "craftsman_automation_ltd", "bucket": "sentinel", "q_bank": craftsman_qs},  # direct-lookup (NP)
]

def llm_judge_grade(question, expected_answer, actual_answer):
    """Call OpenAI GPT-4o-mini to grade the actual answer against expected answer."""
    import openai
    prompt = f"""You are an expert financial auditor grading a RAG model's answer.
    
    Question: {question}
    Expected (Ground Truth): {expected_answer}
    Actual Answer: {actual_answer}
    
    Determine if the actual answer is correct and complete relative to the expected answer.
    If the actual answer matches the key facts and numbers in the expected answer, rate it as "Pass".
    If there are significant numerical errors, hallucinations, or missing critical context, rate it as "Fail".
    
    Return ONLY a JSON object: {{"grade": "Pass"}} or {{"grade": "Fail", "reason": "why it failed"}}"""
    
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        return result.get("grade", "Fail"), result.get("reason", "")
    except Exception as e:
        print(f"Error grading answer with LLM: {e}")
        return "Fail", str(e)

def main():
    print(f"Running mini-benchmark on {len(QUESTIONS_TO_RUN)} questions against {API_URL}...")
    
    results_table = []
    
    for item in QUESTIONS_TO_RUN:
        q_id = item["id"]
        company = item["company"]
        bucket = item["bucket"]
        q_bank = item["q_bank"]
        
        q_meta = q_bank[q_id]
        question_text = q_meta["question"]
        expected_answer = q_meta["expected_answer"]
        
        print(f"Running Q{q_id} ({company})...")
        
        start_time = time.time()
        try:
            resp = requests.post(API_URL, json={
                "question": question_text,
                "company_slug": company
            }, timeout=300)
            latency = time.time() - start_time
            
            if resp.status_code == 200:
                payload = resp.json()
                actual_answer = payload.get("answer", "")
                grade, reason = llm_judge_grade(question_text, expected_answer, actual_answer)
            else:
                actual_answer = f"API Error: {resp.status_code} - {resp.text}"
                grade, reason = "Fail", "HTTP Error"
        except Exception as e:
            latency = time.time() - start_time
            actual_answer = f"Exception: {e}"
            grade, reason = "Fail", "Timeout or network exception"
            
        results_table.append({
            "id": f"Q{q_id}",
            "company": company.split("_")[0],
            "bucket": bucket,
            "grade": grade,
            "latency": latency,
            "actual_answer": actual_answer,
            "reason": reason
        })
        
    # Output the table in markdown format
    md_lines = []
    md_lines.append("# Mini Benchmark Baseline Results")
    md_lines.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append("")
    md_lines.append("| ID | Company | Bucket | Grade | Latency (s) | Reason if Fail | Actual Answer Snippet |")
    md_lines.append("|---|---|---|---|---|---|---|")
    
    for r in results_table:
        ans_snippet = r["actual_answer"].replace("\n", " ").replace("|", "\\|")
        if len(ans_snippet) > 80:
            ans_snippet = ans_snippet[:80] + "..."
        md_lines.append(f"| {r['id']} | {r['company']} | {r['bucket']} | {r['grade']} | {r['latency']:.2f}s | {r['reason']} | {ans_snippet} |")
        
    md_lines.append("")
    md_lines.append("## Full Answers Details")
    md_lines.append("")
    for r in results_table:
        md_lines.append(f"### {r['id']} ({r['company']} - {r['bucket']}) - {r['grade']}")
        md_lines.append(f"- **Latency**: {r['latency']:.2f}s")
        md_lines.append(f"- **Reason if Fail**: {r['reason']}")
        md_lines.append("#### Actual Answer:")
        md_lines.append(r["actual_answer"])
        md_lines.append("")
        
    output_file = "d:/FinBot/tests/results/mini_benchmark_baseline.md"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    print("\nBenchmark completed. Results written to:", output_file)
    
    # Print the markdown table to console
    print("\n".join(md_lines[:25]))

if __name__ == "__main__":
    main()
