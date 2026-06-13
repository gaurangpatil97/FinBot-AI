# Phase A Baseline Results

**Commit Hash:** `e9f8dacd5e477fe2633e182bfb702711a710d85a`
**Timestamp:** `2026-06-13 14:05:22` (Source: `20260613_130745`)

## 1. Router Accuracy
- **Overall Lenient:** 71/77 (92.2%)
- **Overall Strict:** 48/77 (62.3%)

**Per Section (Lenient):**
- **Excel:** 15/15 (100%)
- **Concall:** 15/15 (100%)
- **PDF:** 16/16 (100%)
- **Images:** 12/16 (75%)
- **Cross:** 13/15 (87%)

## 2. Answer Accuracy (Raw)
*Note: Pending manual review.*
- **Overall:** Not Reviewed (0/77)
- **Excel:** Not Reviewed (0/15)
- **Concall:** Not Reviewed (0/15)
- **PDF:** Not Reviewed (0/16)
- **Images:** Not Reviewed (0/16)
- **Cross:** Not Reviewed (0/15)

## 3. RAGAS Scores
*Evaluated 77 questions (308 LLM calls). No NaN rows were encountered in the evaluation dataset.*

| Metric | Score | NaNs Count |
| :--- | :--- | :--- |
| **Faithfulness** | 0.6296 | 0 |
| **Answer Relevancy** | 0.7025 | 0 |
| **Context Recall** | 0.2978 | 0 |
| **Context Precision** | 0.3672 | 0 |

## 4. Latency
*Time in seconds.*

| Section | Avg | Median | P95 | Worst-Case |
| :--- | :--- | :--- | :--- | :--- |
| **Excel** | 14.17 | 10.66 | 30.59 | 43.90 |
| **Concall** | 12.82 | 13.03 | 16.40 | 16.59 |
| **PDF** | 12.43 | 11.24 | 19.20 | 21.95 |
| **Images** | 12.60 | 11.90 | 19.07 | 29.18 |
| **Cross** | 14.84 | 14.29 | 23.77 | 24.16 |
| **Overall** | 13.35 | - | - | 43.90 |

## 5. Failure Analysis

### Routing Failures (6)
- **Q59 [Images]:** Expected `['images']` | Got `['pdf']`
- **Q60 [Images]:** Expected `['images']` | Got `['pdf']`
- **Q61 [Images]:** Expected `['images']` | Got `['pdf']`
- **Q62 [Images]:** Expected `['images']` | Got `['pdf']`
- **Q69 [Cross]:** Expected `['excel', 'pdf', 'images']` | Got `['excel']`
- **Q75 [Cross]:** Expected `['excel', 'pdf', 'concall']` | Got `['excel', 'pdf']`

### Citation Failures (4)
- **Q6 [Excel]:** Compute the Debt-to-Equity ratio for FY25 and FY26 and asses...
- **Q7 [Excel]:** Calculate Debtor Days for FY23 and FY26 and compare receivab...
- **Q8 [Excel]:** Compute the Interest Coverage Ratio for FY22 and FY25 and ev...
- **Q64 [Cross]:** The FY23 MD&A states the Interest Coverage Ratio declined fr...

### Answer Failures (0)
- *Pending manual review of all 77 questions.*
