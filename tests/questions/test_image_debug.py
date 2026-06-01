"""
Image routing debug subset of 150Q benchmark
Runs a selected set of image questions from the 150Q benchmark and saves results to JSON.
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

# Reuse constants and QA data from the master 150Q file
from test150Q_craftsmanAutomation import QA_PAIRS, check_match, BASE_URL, TIMEOUT

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "results"

# Selected question IDs to debug image routing
SELECTED_IDS = [34, 35, 36, 37, 38, 40, 42, 43, 44, 45, 46, 47, 48, 49, 51, 52, 53, 54, 55, 56, 57, 59]

QA_SUBSET = [qa for qa in QA_PAIRS if qa["id"] in SELECTED_IDS]


def run_test():
    print("\n" + "="*80)
    print("IMAGE ROUTING DEBUG — SUBSET OF 150Q")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    results = []
    section_scores = {"Image": {"correct": 0, "total": 0}}

    for qa in QA_SUBSET:
        q_id = qa["id"]
        section = qa["section"]
        question = qa["question"]
        expected_source = qa["expected_source"]

        print(f"\n{'─'*70}")
        print(f"Q{q_id:03d} [{section}] {question}")
        print(f"Expected source: {expected_source}")

        try:
            response = requests.post(
                BASE_URL,
                json={"question": question, "company_slug": "craftsman_automation_ltd"},
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No answer")
                citations = data.get("citations", [])
                agent = data.get("agent_used", "unknown")

                # Extract filenames from citations
                cited_files = []
                for c in citations:
                    if isinstance(c, dict):
                        cited_files.append(c.get("filename", ""))
                        cited_files.append(c.get("collection", ""))
                    elif isinstance(c, str):
                        cited_files.append(c)

                matched = check_match(expected_source, cited_files)

                print(f"ANSWER: {answer[:300]}{'...' if len(answer) > 300 else ''}")
                print(f"AGENT: {agent}")
                print(f"CITATIONS: {cited_files[:3]}")
                print(f"MATCH: {'✅ YES' if matched else '❌ NO'}")

                section_scores[section]["total"] += 1
                if matched:
                    section_scores[section]["correct"] += 1

                results.append({
                    "id": q_id,
                    "section": section,
                    "question": question,
                    "answer": answer,
                    "citations": cited_files,
                    "matched": matched,
                    "agent": agent
                })

            else:
                print(f"ERROR: HTTP {response.status_code}")
                results.append({
                    "id": q_id,
                    "section": section,
                    "question": question,
                    "answer": f"HTTP {response.status_code}",
                    "citations": [],
                    "matched": False,
                    "error": True,
                    "agent": "unknown"
                })
                section_scores[section]["total"] += 1

        except requests.exceptions.Timeout:
            print(f"TIMEOUT after {TIMEOUT}s")
            results.append({
                "id": q_id,
                "section": section,
                "question": question,
                "answer": "TIMEOUT",
                "citations": [],
                "matched": False,
                "timeout": True,
                "agent": "unknown"
            })
            section_scores[section]["total"] += 1

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "id": q_id,
                "section": section,
                "question": question,
                "answer": f"ERROR: {e}",
                "citations": [],
                "matched": False,
                "error": True,
                "agent": "unknown"
            })
            section_scores[section]["total"] += 1

        time.sleep(0.5)

    # Summary
    total_correct = sum(s["correct"] for s in section_scores.values())
    total_questions = sum(s["total"] for s in section_scores.values())

    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    for section, scores in section_scores.items():
        if scores["total"] > 0:
            pct = scores["correct"] / scores["total"] * 100
            print(f"{section:<15} {scores['correct']}/{scores['total']:<8} {pct:.1f}%")

    overall_pct = total_correct / total_questions * 100 if total_questions > 0 else 0
    print(f"TOTAL {total_correct}/{total_questions} {overall_pct:.1f}%")

    # Save results to JSON as requested
    json_path = OUTPUT_DIR / "image_debug_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_score": f"{total_correct}/{total_questions}",
            "section_scores": section_scores,
            "results": results
        }, f, indent=2)

    print(f"\nDetailed results saved to: {json_path}")


if __name__ == "__main__":
    run_test()
