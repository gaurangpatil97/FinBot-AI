import sys

file_path = r"D:\FinBot\benchmarks\runs\run_001\FINAL_baseline_summary.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Changelog update
changelog_addition = "| 2026-07-05 | Fixed Top-K=3 vector search truncation for Excel (missing years) via FULL_TIME_SERIES full-chunk retrieval; fixed resulting CE-question context-saturation regression via SPECIFIC_YEARS metadata-filtered retrieval; both verified via genuine manual grading (after rejecting two automated-grading attempts that gave false results). | Excel+Ratio+CE Strict Acc (Astral / Craftsman) | 11/30 (36%) / 9/30 (30%) | 28/30 (93%) / 26/30 (86%) (Total Strict: Astral 34% -> 51%, Craftsman 24% -> 41%) |\n"

# find end of changelog
idx = content.find("## 1. Methodology Note")
content = content[:idx] + changelog_addition + "\n" + content[idx:]

# 2. Overall Scores (Both Companies) — CORRECTED
# Astral: Strict 34.0% -> 51.0%, Lenient 68.0% -> 76.0%
# Craftsman: Strict 24.0% -> 41.0%, Lenient 53.0% -> 67.0%
content = content.replace("| **Astral Ltd** | 91.0% | 90.0% | 34.0% | 68.0% |", "| **Astral Ltd** | 91.0% | 90.0% | 51.0% | 76.0% |")
content = content.replace("| **Craftsman Automation** | 86.0% | 61.0% | 24.0% | 53.0% |", "| **Craftsman Automation** | 86.0% | 61.0% | 41.0% | 67.0% |")

# 3. Per-Section Breakdown
# Astral Excel: 55.0% -> 90.0%, 80.0% -> 95.0%
# Astral Ratio: 0.0% -> 100.0%, 50.0% -> 100.0%
content = content.replace("| Excel | 20 | 100.0% | 100.0% | 55.0% | 80.0% | 0.8397 | 0.1234 |", "| Excel | 20 | 100.0% | 100.0% | 90.0% | 95.0% | 0.8397 | 0.1234 |")
content = content.replace("| Ratio | 10 | 100.0% | 100.0% | 0.0% | 50.0% | 0.7887 | 0.1210 |", "| Ratio | 10 | 100.0% | 100.0% | 100.0% | 100.0% | 0.7887 | 0.1210 |")

# Craftsman Excel: 45.0% -> 80.0%, 65.0% -> 95.0%
# Craftsman Ratio: 0.0% -> 100.0%, 20.0% -> 100.0%
content = content.replace("| Excel | 20 | 100.0% | 85.0% | 45.0% | 65.0% | 0.8031 | 0.3729 |", "| Excel | 20 | 100.0% | 85.0% | 80.0% | 95.0% | 0.8031 | 0.3729 |")
content = content.replace("| Ratio | 10 | 100.0% | 100.0% | 0.0% | 20.0% | 0.8403 | 0.1379 |", "| Ratio | 10 | 100.0% | 100.0% | 100.0% | 100.0% | 0.8403 | 0.1379 |")

# 4. Key Findings Update
old_finding_1 = "1. **Zero confirmed backend/RAG bugs found tonight — all gaps traced to benchmark measurement/ground-truth errors, now corrected.** The previous iteration indicated catastrophic citation retrieval rates and severe routing gaps. Upon deep investigation, the retrieval and routing systems were functioning exceptionally well across source types. The failures were pure measurement artifacts caused by strict regex bounds in the evaluation script, missing collection names, contaminated agnostic questions (Astral vocabulary tested against Craftsman), and bad ground-truth filenames."

new_finding_1 = "1. **Two Major Genuine System Fixes Confirmed:** Distinct from earlier measurement-bug corrections, two real backend fixes drove the massive jump in Strict accuracy today. First, re-ingesting Concalls fixed the broken speaker Q&A parsing. Second, the Excel dual-routing fix (`FULL_TIME_SERIES` vs `SPECIFIC_YEARS` via metadata filtering) successfully eliminated the Top-K truncation bug while preventing context saturation, driving Excel/Ratio accuracy from near-zero to near-perfect.\n\n2. **Remaining Excel Gaps are Qualitative, Not Retrieval:** While numeric extraction is now largely flawless (E and R sections), the remaining gaps in CE (Company-Specific) questions are qualitative LLM synthesis failures. For example: Astral CE8 missed the correct year-window and capex figure; Craftsman CE4 extracted the wrong margin metric; and Craftsman CE7/CE9/CE10 all demonstrated a pattern where the LLM reasons correctly but omits a specifically-required stated figure or phrase."

content = content.replace(old_finding_1, new_finding_1)

# fix numbering in Key Findings
content = content.replace("2. **Concall Routing Gap", "3. **Concall Routing Gap")
content = content.replace("3. **Astral's True Supremacy", "4. **Astral's True Supremacy")
content = content.replace("4. **Systemic Context Precision Crisis", "5. **Systemic Context Precision Crisis")

# 5. Next Steps Update
next_steps_addition = "\n- **PDF and Concall Improvements:** The PDF and Concall sections remain the next highest-leverage targets for further Strict gains toward a 60% overall target. Craftsman's Concall (still 15% Strict) and PDF (20% Strict) sections are in particular need of attention."

if "- **PDF and Concall Improvements" not in content:
    content = content.replace("sections (currently 0% for both companies).", "sections (currently 0% for both companies)." + next_steps_addition)
    # Fix the outdated ratio note
    content = content.replace("sections (currently 0% for both companies).", "sections (now resolved to 100%).")


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated successfully.")
