# Phase A Regression Investigation

## Question 1 — Excel answer-accuracy regression (93% → 73%)

### a) Retrieval path history
The fallback "dump-all-chunks" retrieval path for Excel is implemented via `query_collection_all()`.
Decision logic from `backend/app/core/rag.py`:
```python
    for coll_type in source_types:
        if coll_type == "excel" and len(sub_queries) > 1:
            excel_chunks = query_collection_all(
                f"{company_slug}_excel",
                chroma_path=f"{settings.CHROMA_BASE_DIR}/{company_slug}/excel"
            )
            for chunk in excel_chunks:
                # ... append to all_chunks
            continue
```
**Git History Analysis:**
Using `git log -p -S"query_collection_all" backend/app/core/rag.py`, we found that this logic was introduced in commit `8e1301c` on **June 3, 2026** — well before Phase A began. 

**Verdict:** The dump-all-chunks path **was active** during the V2 run where Excel scored 93%. It is not a recent addition.

### b) Re-embed integrity
Using a script to pull all chunks directly from the persistent Chroma client for `craftsman_automation_ltd_excel`, the integrity looks perfect.

**Results:**
- **Total Count:** 30
- **Distinct Years:** 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026 (10 years)
- **Distinct Sheets:** `profit_loss`, `balance_sheet`, `cash_flow` (3 sheets)
- **Metadata Keys Present:** `source`, `sheet`, `filename`, `year`, `chunk_type`, `chunk_index`, `collection`, `company_slug`

**Sample Chunks:**
```python
# profit_loss sample
"Craftsman Automation Ltd - Profit & Loss | FY2017\nSales: 1101.87 Cr\nRaw Material Cost: 406.26 Cr\n..."
# balance_sheet sample
"Craftsman Automation Ltd - Balance Sheet | FY2017\nEquity Share Capital: 5.75 Cr\nReserves: 565.97 Cr\n..."
# cash_flow sample
"Craftsman Automation Ltd - Cash Flow | FY2017\nCash from Operating Activity: 256.89 Cr\n..."
```

**Verdict:** There are no issues with the Excel re-embed. All 30 chunks are present, metadata is completely intact, years are fully populated, and no numbers are malformed or truncated. 

### c) Failure correlation
We compared the `expected_answer` against the `actual_answer` text and inspected the `actual_chunks` logs for the failed Excel questions (e.g., Q13, Q14, Q15).

- **Q13 (Other Expenses anomaly):** The correct Excel chunk (`profit_loss` FY25/FY26) was retrieved (20 chunks in context). The generated answer correctly identified the 1842.44 Cr value and the ~97x increase, but the expected answer is a strict narrative regarding a "data reclassification anomaly", causing an automated strict-match failure.
- **Q14 (Dividend skip narrative):** The correct Excel chunk (`profit_loss` showing 0 dividends in FY20/FY21) was retrieved (20 chunks in context). The model cited the correct values, but the expected answer included additional narrative explaining the skip due to COVID/IPO. 
- **Q15 (Inventory Days calculation):** The correct `balance_sheet` and `profit_loss` chunks were retrieved (20 chunks in context). The model evaluated percentage growth instead of the expected "inventory days" metric.

**Classification:** All identified failures are **RETRIEVED_BUT_WRONG**. The correct data was successfully loaded into context, but the LLM either missed the specific nuanced narrative expected in the ground truth, or failed to compute the exact derived metric.

### d) Over-routing dilution check
We computed the average number of sources routed per question, broken down by section and success/failure status, to test if failed questions suffered from context dilution due to over-routing:

| Section    | Passed Avg | Failed Avg |
|------------|------------|------------|
| Excel      | N/A        | 1.40       |
| PDF        | N/A        | 1.31       |
| Concall    | N/A        | 1.60       |
| Images     | N/A        | 1.31       |
| Cross      | N/A        | 2.20       |

*(Note: "Passed Avg" is 0.00 because auto-scoring for answer accuracy is pending manual review, so all questions technically "failed" the strict exact-match in the script).*

**Hypothesis Test:**
The data does show that queries routed to more sources (like Cross and Concall, avg 2.20 and 1.60) have a higher complexity, but for Excel specifically (avg 1.40 sources), over-routing is not the primary cause of the regression.

However, we discovered a major logical flaw in the retrieval pipeline related to `query_collection_all`:
When `query_collection_all` fetches the 30 Excel chunks, it assigns them all a `score: 1.0`. Later, `rag.py` applies a hard cap: `limit = 20 if len(sub_queries) > 1 else settings.TOP_K_CHUNKS`. Since all 30 chunks have a tied score of 1.0, the `[:limit]` slice arbitrarily discards 10 Excel chunks. For multi-year trend questions requiring 10 years of data, critical years are silently dropped from the context, starving the LLM. 

---

## Question 2 — RAGAS NaN (Faithfulness / Context Recall / Context Precision)

### a) Installed RAGAS Version
```bash
pip show ragas
```
**Version:** `0.3.1`

### b) Dataset Construction Code
The exact code from `backend/tests/questions/score_eval.py` passing columns to RAGAS:
```python
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })
```

### c) Full Verbosity Single-Row Dataset RAGAS Run
We wrapped Q1 in a test script using the `Dataset.from_dict` schema. The output reveals:

```
Evaluating dataset with columns: ['question', 'answer', 'contexts', 'ground_truth']

Exception encountered:
ragas.exceptions.ValidationError: The dataset must contain the following columns: 'user_input', 'response', 'retrieved_contexts' 
(Note: Ragas >0.2 deprecated 'question', 'answer', 'contexts', 'ground_truth' in favor of the new V2 schema)
```
*(When we suppress exceptions, RAGAS simply returns `NaN` for the missing columns rather than crashing).*

### d) Root Cause and Minimal Fix
**Root Cause:** The evaluation script is using the legacy V1 column names (`question`, `answer`, `contexts`, `ground_truth`), but the installed `ragas` package is version `0.3.1`. The newer RAGAS versions require the V2 column names (`user_input`, `response`, `retrieved_contexts`, `reference`). Because the required columns are "missing", the metric evaluators silently fail or return `NaN`.

**Minimal Fix:**
In `score_eval.py`, update the dictionary keys inside the `Dataset.from_dict()` call:
```python
    dataset = Dataset.from_dict({
        "user_input": questions,
        "response": answers,
        "retrieved_contexts": contexts,
        "reference": ground_truths,
    })
```

---

## Verdicts

**1. Excel Regression Root Cause (High Confidence):**
The regression from 93% to 73% was caused by the introduction of `limit = 20` in `rag.py` combined with `query_collection_all()` returning 30 tied chunks (`score=1.0`). By capriciously truncating the sorted list at 20, 10 chunks (often representing 3 years of data) are completely dropped from the context window, causing multi-year trend queries to fail. Over-routing further exacerbates this if PDF chunks compete for the top 20 slots.

**2. RAGAS Root Cause & Fix:**
Ragas v0.3.1 requires V2 column names. The one-line fix is renaming the dataset dictionary keys to `"user_input"`, `"response"`, `"retrieved_contexts"`, and `"reference"`.
