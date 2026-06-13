# PDF & Concall Failure Analysis

Based on a read-only diagnostic of the `tests/results/eval_raw_results_20260612_192735.json` evaluation data, here is the breakdown of why the PDF and Concall section questions failed.

## Failure Classification Summary

| Section | Total Failures | NOT_RETRIEVED | RETRIEVED_BUT_WRONG |
|---|---|---|---|
| **PDF** | 9 | 2 (22%) | 7 (78%) |
| **Concall** | 7 | 7 (100%) | 0 (0%) |

### Key Findings:
- **Concall Failures:** 100% of the concall failures were **NOT_RETRIEVED**. An inspection of the `actual_chunks` reveals that the system almost exclusively retrieved *Excel structured data chunks* (e.g., Profit & Loss sheets) instead of the actual earnings call transcripts. Because the management commentary and guidance narratives were completely absent from the context, the LLM was forced to either infer from numbers or decline to answer.
- **PDF Failures:** 78% of the PDF failures were **RETRIEVED_BUT_WRONG**. The relevant text (including specific numbers like derivative asset carrying values or exact MD&A quotes) was successfully retrieved and present in the chunks, but the LLM failed to synthesize or extract the correct answer, indicating a generation or context-dilution issue.

---

## Example `RETRIEVED_BUT_WRONG` Cases (PDF)

Here are three examples where the necessary information was confirmed to be present in the retrieved context, yet the final generation failed:

**1. FY22 Auditor Key Audit Matters (Derivative Contracts)**
* **Question:** The company's FY22 auditor identified two Key Audit Matters. What are they, and for the derivative contracts KAM, what is the combined carrying value of derivative assets and liabilities?
* **Context Size:** 20 total chunks.
* **Relevant Chunk Position:** **Chunk 0** (Very Top)
* **What Happened:** The exact numbers for the derivative assets (₹855 Lakhs) and liabilities (₹538 Lakhs) were present in the absolute highest-scoring chunk. However, the LLM failed to extract them properly, incorrectly stating "₹ 0.00 Cr (no derivative assets reported)".

**2. FY22 Directors' Report Risk Management (Funding Risk)**
* **Question:** In the company's FY22 Directors' Report under Risk Management, what is the stated mitigation strategy against Funding Risk, and does the metric cited match the MD&A Key Ratios table?
* **Context Size:** 20 total chunks.
* **Relevant Chunk Position:** **Chunk 2** (Near Top)
* **What Happened:** The specific mitigation metrics (Debt-Equity of 0.63x and net cash of ₹322 Cr) were successfully retrieved in the 3rd chunk. The LLM provided a generic summary of funding risk mitigation but failed to cite the exact numerical metrics required by the expected answer.

**3. FY23 MD&A Interest Coverage Ratio Decline**
* **Question:** According to the MD&A of the company for FY23, what was the stated reason for the decline in the Interest Coverage Ratio, and what does this imply about financing risk?
* **Context Size:** 14 total chunks.
* **Relevant Chunk Position:** **Chunk 5** (Middle)
* **What Happened:** The explicit reason for the ICR decline (interest cost increasing from ₹84 Cr to ₹117 Cr due to the DR Axion acquisition) was present mid-way through the context. The LLM explicitly stated: *"The context provided does not contain any explicit mention or discussion... about the Interest Coverage Ratio,"* indicating it completely lost or overlooked the information buried in the middle chunks.
