"""
FinBot Gate-Test: Images CI1-CI10 Subset
Runs only the 10 Images questions for both Astral and Craftsman.
Saves results per-company to tests/results/ for manual review.
"""

import json
import time
import requests
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api/v1/query"
RESULTS_DIR = Path("tests/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


# ── Import the full question banks ────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from Astral_questions_run_eval import QUESTIONS as ASTRAL_ALL
from final_craftsman_automation_run_eval import QUESTIONS as CRAFTSMAN_ALL


def get_images_questions(full_list):
    return [q for q in full_list if q.get("section") == "Images"][:10]


def fire_question(question: str, company_slug: str) -> dict:
    payload = {"question": question, "company_slug": company_slug}
    try:
        response = requests.post(API_URL, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  Error {response.status_code}: {response.text[:200]}")
            return {}
    except Exception as e:
        print(f"  Failed: {e}")
        return {}


def check_citation(actual_citations: list, expected_contains: list) -> bool:
    if not expected_contains:
        return True
    if not actual_citations:
        return False
    citation_filenames = []
    for citation in actual_citations:
        if isinstance(citation, dict):
            fname = citation.get("source_url", "") or citation.get("filename", "") or citation.get("source_uri", "")
            if fname.startswith("http") or fname.startswith("file") or "\\" in fname or "/" in fname:
                fname = Path(fname).name
        else:
            fname = Path(str(citation)).name
        citation_filenames.append(fname)
    citation_str = " ".join(citation_filenames).lower()
    return any(term.lower() in citation_str for term in expected_contains)


def run_company(company_name, company_slug, questions, out_file):
    print(f"\n{'='*60}")
    print(f"  {company_name} — Images CI1-CI{len(questions)}")
    print(f"{'='*60}\n")

    results = []
    for i, q in enumerate(questions, 1):
        qid = f"CI{i}"
        print(f"  [{qid}] {q['question'][:80]}...")
        resp = fire_question(q["question"], company_slug)

        cit_ok = check_citation(
            resp.get("citations", []),
            q.get("expected_citation_contains", [])
        )

        # Extract citation filenames for output
        actual_cit_names = []
        for c in resp.get("citations", []):
            if isinstance(c, dict):
                actual_cit_names.append(c.get("filename", "?"))

        result = {
            "question_id": qid,
            "section": "Images",
            "question": q["question"],
            "expected_answer": q["expected_answer"],
            "actual_answer": resp.get("answer", ""),
            "expected_citations": q.get("expected_citation_contains", []),
            "actual_citations": resp.get("citations", []),
            "actual_citation_filenames": actual_cit_names,
            "citation_correct": cit_ok,
            "collections_searched": resp.get("collections_searched", []),
            "agent_used": resp.get("agent_used", ""),
            "latency_seconds": resp.get("latency_seconds", 0),
        }
        results.append(result)
        status = "CIT_OK" if cit_ok else "CIT_FAIL"
        print(f"         {status} | {resp.get('latency_seconds', 0):.1f}s | cites: {actual_cit_names[:3]}")
        time.sleep(1)

    # Save JSON
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"company": company_name, "timestamp": TIMESTAMP, "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved to {out_file}")

    # Print summary
    cit_total = sum(1 for r in results if r["citation_correct"])
    print(f"  Citation accuracy: {cit_total}/{len(results)}")
    return results


if __name__ == "__main__":
    astral_qs = get_images_questions(ASTRAL_ALL)
    craftsman_qs = get_images_questions(CRAFTSMAN_ALL)

    print(f"Found {len(astral_qs)} Astral and {len(craftsman_qs)} Craftsman image questions")

    astral_out = RESULTS_DIR / f"gate_images_astral_{TIMESTAMP}.json"
    craftsman_out = RESULTS_DIR / f"gate_images_craftsman_{TIMESTAMP}.json"

    run_company("Astral Ltd", "astral_ltd", astral_qs, astral_out)
    run_company("Craftsman Automation", "craftsman_automation_ltd", craftsman_qs, craftsman_out)

    print(f"\n{'='*60}")
    print(f"  GATE TEST COMPLETE")
    print(f"  Astral:    {astral_out}")
    print(f"  Craftsman: {craftsman_out}")
    print(f"{'='*60}")
