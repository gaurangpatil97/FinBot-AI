# Concall & PDF Generation Failure Analysis

Based on the evaluation of the Concall and PDF questions (where routing was 100% accurate), we have diagnosed the generation failures. While some failures are still rooted in incomplete retrieval (the specific chunk containing the answer was not fetched despite correct routing), many failures occur even when the necessary information is present or partially present.

Here is the categorization of the failures:

## 1. Chunk present, LLM ignored/missed it (Attention/Formatting Issue)

In these cases, the LLM successfully retrieved the factual data but ignored the specific analytical or forensic implication requested by the prompt.

* **Example 1: Q25 (Concall) - Bonus Provisions**
  * **Question:** Asked to identify two specific one-offs regarding staff costs and what pattern they reveal about inter-quarter EBITDA comparisons.
  * **Expected:** Highlight that bonus recognition is being shifted between quarters (Q3 FY22 release vs Q1 FY23 early provision), creating a risk of distorted inter-quarter EBITDA comparisons.
  * **Actual Answer:** The LLM correctly lists the two one-offs (Q3 FY22 ₹7 Cr release, Q1 FY23 payment) but completely ignores the second half of the question regarding the analytical implication (distorted EBITDA).
  * **Diagnosis:** The LLM focused entirely on data extraction and dropped the reasoning/analytical task.

* **Example 2: Q42 (PDF) - DR Axion Consolidation**
  * **Question:** Asked about the DR Axion acquisition (acquired Feb 2023) and its impact on FY24 consolidated optics.
  * **Expected:** Note that DR Axion contributed a full year of ₹1,246 Cr revenue in FY24 vs only 2 months in FY23, inflating consolidated YoY growth optics.
  * **Actual Answer:** The LLM notes that the short acquisition history creates potential for insufficient due diligence, but completely misses the core financial impact (base-period asymmetry of 2 months vs 12 months inflating growth).
  * **Diagnosis:** The LLM hallucinates a generic "due diligence risk" instead of performing the required date-based reasoning present in the text.

## 2. Chunk present, LLM misread/miscalculated (Reasoning Issue)

In these cases, the LLM hallucinates or forces an incorrect calculation from the wrong data points because it misinterprets the text.

* **Example 1: Q20 (Concall) - Debt-to-EBITDA Ratio**
  * **Question:** Calculate the Debt-to-EBITDA ratio for FY23 H1 as disclosed by management.
  * **Expected:** H1 FY23 Debt-to-EBITDA = 1.08x.
  * **Actual Answer:** 1.17:1.
  * **Chunk Text:** *"The Q1 number if you are extrapolating for the full year, debt-to-EBITDA is 1.17:1 which is an improvement from 1.33 for the last year..."*
  * **Diagnosis:** The LLM misread "Q1" as "H1" and grabbed the 1.17:1 ratio instead of recognizing that the exact H1 ratio was missing from the chunk, forcing an incorrect answer.

* **Example 2: Q32 (PDF) - Highest Ratio Change**
  * **Question:** Which specific financial ratio showed the highest year-on-year percentage change in FY22?
  * **Expected:** Interest Coverage Ratio (+53%).
  * **Actual Answer:** Return on Equity (ROE) (+34%).
  * **Diagnosis:** The chunk containing the Interest Coverage Ratio was missed by the retriever. Instead of stating the data was incomplete, the LLM calculated the changes for the ratios it *did* have in its chunks (like ROE) and confidently declared it the highest overall.

## 3. Chunk present but format makes it hard to parse

Concall transcripts are often raw prose dumps. When financial figures are embedded in conversational text without clear labels, the LLM struggles to parse them accurately.

* **Example 1: Q16 (Concall) - Total Consolidated Revenue**
  * **Question:** What was the total consolidated H1 FY23 revenue?
  * **Expected:** ₹1,447 crores.
  * **Actual Answer:** ₹199 crore.
  * **Chunk Text:** *"Storage solutions for FY22 as a whole was 253... and this year H1 FY23 has been 199."*
  * **Diagnosis:** Because the chunks lack structured tables and speaker labels are separated from context, the LLM latched onto the only "H1 FY23" number it found (₹199 Cr), failing to realize this was only for the Storage Solutions segment, not the consolidated total.

* **Example 2: Q18 (Concall) - Segment-wise EBIT**
  * **Question:** What was the segment-wise EBIT for Auto Powertrain, Aluminum Products, and I&E in FY23 Q1?
  * **Expected:** Auto Powertrain: ₹95 Cr; Aluminum: ₹20 Cr; I&E: ₹11 Cr.
  * **Actual Answer:** "The segment-wise EBIT for FY23 Q1 is not explicitly provided in the context."
  * **Chunk Text:** The text contains various overlapping segment numbers (e.g., *"value addition on Q2 FY22 on auto powertrain was 88 crore..."*). 
  * **Diagnosis:** The dense, conversational dumping of numbers across multiple quarters and segments overwhelms the LLM. Without a tabular format, it cannot reliably extract the specific Q1 EBIT components and simply gives up.
