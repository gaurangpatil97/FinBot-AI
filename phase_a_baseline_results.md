# Phase A Baseline Results

**Run Metadata**
- **Git Commit:** 451476b
- **Date/Time:** 2026-06-12 20:03
- **Total Runtime:** ~25 minutes (17s avg latency per query over 77 questions)
- **Model:** Default (backend standard)

## 2. Router Accuracy

| Section | Lenient (Correct / Total) | Strict (Correct / Total) | Fallbacks Fired |
|---------|---------------------------|--------------------------|-----------------|
| Excel | 15/15 (100.0%) | 9/15 (60.0%) | 0 |
| PDF | 16/16 (100.0%) | 11/16 (68.8%) | 0 |
| Concall | 15/15 (100.0%) | 7/15 (46.7%) | 0 |
| Images | 12/16 (75.0%) | 8/16 (50.0%) | 0 |
| Cross | 14/15 (93.3%) | 14/15 (93.3%) | 0 |
| **Overall** | **72/77 (93.5%)** | **49/77 (63.6%)** | **0** |

## 3. Answer Accuracy

*Pending manual review.* 
(All 77 questions are currently un-graded. A handoff file `tests/results/eval_manual_review_handoff.json` has been generated containing only the fields required for manual human review, with a null `correct` field ready to be filled.)

## 4. RAGAS Scores

- **Faithfulness:** `nan`
- **Answer Relevancy:** 0.6741
- **Context Recall:** `nan`
- **Context Precision:** `nan`

**Scoring Details:**
- **Rows Evaluated:** 77
- **Rows Excluded:** 0 (All rows had retrieved chunks, so none were skipped for `contexts=[]`)

> [!WARNING]
> Faithfulness, Context Recall, and Context Precision returned `NaN` across the evaluation dataset. Here is the `contexts` structure being passed to RAGAS for an offending row (Q1):
> ```json
> [
>   "Craftsman Automation Ltd - Profit & Loss | FY2026\nSales: 8069.27 Cr\nRaw Material Cost: 4525.39 Cr\nChange in Inventory: 123.43 Cr\nEmployee Cost: 587.28 Cr\nOther Expenses: 1842.44 Cr\nOther Income: 49.53 Cr\nDepreciation: 443.85 Cr\nInterest: 308.97 Cr\nProfit before tax: 534.30 Cr\nTax: 150.31 Cr\nNet profit: 383.99 Cr\nDividend Amount: 26.84 Cr\nEBITDA: 1114.16 Cr"
> ]
> ```
> The contexts list is correctly populated as a list of strings (`List[str]`).

## 5. Latency

**Aggregates:**
- **Average:** 17.08s
- **Median:** 15.15s
- **P95:** 30.33s
- **Worst-case:** 45.57s

**Average per Section:**
- **Excel:** 18.00s
- **PDF:** 14.14s
- **Concall:** 21.24s
- **Images:** 14.47s
- **Cross:** 17.90s

## 6. Failures & Exceptions

**Routing Failures (Lenient):**
- **Q59:** The segment-wise performance table in the MD&A of the FY25 annual report...
  - **Expected:** `['images']` | **Routed:** `['pdf']`
- **Q60:** The Key Financial Ratios comparison table in the FY25 MD&A shows two ratios...
  - **Expected:** `['images']` | **Routed:** `['pdf']`
- **Q61:** The BRSR Section 9 table in the FY25 report shows the number of training pro...
  - **Expected:** `['images']` | **Routed:** `['pdf']`
- **Q62:** The commodity price risk and hedging table in the FY25 Corporate Governance...
  - **Expected:** `['images']` | **Routed:** `['pdf']`
- **Q69:** The FY24 annual report donut chart shows Aluminum Products contributing to 1...
  - **Expected:** `['excel', 'pdf', 'images']` | **Routed:** `['excel']`

**Exceptions:**
- None. (Zero questions threw internal server errors or returned `ERROR:` string outputs).
