# FinBot Model Comparison Experiment Report

## Overview
This report documents a side-by-side performance and quality experiment comparing the production default model (**GPT-4.1-mini**) against **GPT-4o-mini** across the FinBot evaluation pipeline. The objective was to determine whether a model downgrade could reduce operating costs and latency without compromising accuracy and agentic tool-routing quality.

## Experiment Setup
* **Mini Benchmark**: A stratified subset of 15 questions extracted from the full 77-question CA-level benchmark (3 questions per section: Excel, Concall, PDF, Images, Cross; 1 question per difficulty: Easy, Medium, Hard).
* **Models Compared**: 
  - **Baseline**: GPT-4.1-mini (current default)
  - **Experimental**: GPT-4o-mini
* **Swap Scope**: Clarifier agent query decomposition ([clarifier_agent.py](file:///d:/FinBot/backend/app/core/clarifier_agent.py)), router agent source selection ([router_agent.py](file:///d:/FinBot/backend/app/core/router_agent.py)), calculation agent classification and parsing ([calculation_agent.py](file:///d:/FinBot/backend/app/core/calculation_agent.py)), chart generation planning ([chart_builder.py](file:///d:/FinBot/backend/app/core/chart_builder.py)), and answer synthesis/guardrails ([rag.py](file:///d:/FinBot/backend/app/core/rag.py)).
* **Date**: 29 June 2026

---

## Results Summary Table

| Metric | GPT-4.1-mini (Baseline) | GPT-4o-mini (Experimental) | Change |
| :--- | :---: | :---: | :---: |
| **Routing Accuracy (Strict)** | 100.0% (15/15) | 46.7% (7/15) | -53.3% |
| **Overall Citation Accuracy** | 100.0% (15/15) | 66.7% (10/15) | -33.3% |
| **Average Latency** | 24.28s | 9.25s | -15.03s (2.6x faster) |
| **Min Latency** | 10.19s | 3.04s | -7.15s |
| **Max Latency** | 45.42s | 19.96s | -25.46s |
| **RAGAS Faithfulness** | 0.6968 | 0.6731 | -0.0237 |
| **RAGAS Answer Relevancy** | 0.7788 | 0.8232 | +0.0444 |
| **RAGAS Context Recall** | 0.1956 | 0.1212 | -0.0744 |
| **RAGAS Context Precision** | 0.2012 | 0.2603 | +0.0591 |
| **Hallucination Rate** | 30.32% | 32.69% | +2.37% |
| **Retrieval F1@K** | 0.9040 | 0.7907 | -0.1133 |
| **Total Cost (15 Qs)** | $0.016350 | $0.010630 | -$0.005720 (35% reduction) |
| **Total Tokens** | 86,772 | 60,276 | -26,496 |

---

## Per-Question Comparison Table

| QID | Section | Difficulty | Question | GPT-4.1-mini Answer | GPT-4o-mini Answer | Routing Match? (Base / New) | Latency Diff (Base - New) |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **1** | Excel | Easy | What was the Net Profit reported by the company... | ## Summary The Net Profit reported by Craftsman Automation Ltd in FY2026 was ₹383.99 crore.  ## D... | I can only answer financial questions about the company corpus. Please ask about financials, annu... | Base: ✅ / New: ❌ | 24.62s |
| **5** | Excel | Medium | Calculate the Operating Profit Margin for FY24 ... | ## Summary   The Operating Profit Margin (OPM) for FY24 is approximately 15.9%, and for FY25 it i... | I can only answer financial questions about the company corpus. Please ask about financials, annu... | Base: ✅ / New: ❌ | 41.86s |
| **9** | Excel | Hard | In FY25, sales grew 27.8% YoY yet PBT fell 39.4... | ## Summary   In FY25, despite a 27.8% year-on-year sales growth, Craftsman Automation’s Profit Be... | ## Summary In FY25, the profit before tax (PBT) fell by 39.4% to ₹127.55 Crores despite a 27.8% i... | Base: ⚠️ / New: ❌ | -0.88s |
| **16** | Concall | Easy | What was the total consolidated H1 FY23 revenue... | ## Summary   The total consolidated revenue for H1 FY23 was ₹398 crore, which exceeded H1 FY22 re... | ## Summary The total consolidated H1 FY23 revenue reported by the company was ₹199 crores, which ... | Base: ✅ / New: ✅ | 9.88s |
| **20** | Concall | Medium | Calculate the Debt-to-EBITDA ratio for FY23 H1 ... | ## Summary   Management disclosed a Debt-to-EBITDA ratio of 1.17:1 for FY23 Q1 (which can be extr... | ## Summary The Debt-to-EBITDA ratio for FY23 H1 is approximately 1.17, while the prior full-year ... | Base: ⚠️ / New: ⚠️ | 2.82s |
| **24** | Concall | Hard | Management claimed in FY23 Q1 that the company'... | ## Summary   Management reported an annualized pre-tax ROCE of 26% in FY23 Q1, up from 20% in the... | ## Summary Management reported an annualized pre-tax ROCE of 26% for FY23 Q1, up from 20% in the ... | Base: ⚠️ / New: ✅ | 7.11s |
| **31** | PDF | Easy | What specific operating model does the company'... | ## Summary   The Chairman describes the company's unique operating model as one that provides exc... | ## Summary The Chairman describes the company's unique operating model as one that provides a "sp... | Base: ✅ / New: ✅ | 0.99s |
| **32** | PDF | Medium | In the company's FY22 MD&A, which specific fina... | ## Summary   The Debt Service Coverage Ratio showed the highest year-on-year percentage increase ... | I can only answer financial questions about the company corpus. Please ask about financials, annu... | Base: ✅ / New: ❌ | 8.17s |
| **33** | PDF | Hard | The company's FY22 auditor identified two Key A... | ## Summary   The company's FY22 auditor identified two Key Audit Matters (KAMs): (1) accounting f... | ## Summary The two Key Audit Matters identified by the auditor for FY22 are the accounting for de... | Base: ⚠️ / New: ⚠️ | 10.99s |
| **47** | Images | Easy | In the About the company infographic page of th... | ## Summary   The three business segments shown in the FY22 annual report infographic and their re... | ## Summary The three business segments shown in the FY22 annual report infographic and their resp... | Base: ✅ / New: ✅ | 5.79s |
| **49** | Images | Medium | In the KPI Position section bar charts of the F... | ## Summary   The Debt/EBITDA ratio shows a declining trend over the five-year period from FY18 to... | ## Summary The Debt/EBITDA ratio showed a decreasing trend from FY18 to FY22, indicating improved... | Base: ✅ / New: ✅ | 29.95s |
| **50** | Images | Hard | In the FY22 annual report, opening pages contai... | ## Summary   The Revenue CAGR of 11% from FY18 to FY22 is accompanied by a caveat that it is calc... | ## Summary The Revenue CAGR infographic notes that the revenue growth figure excludes excise duty... | Base: ⚠️ / New: ❌ | 14.26s |
| **63** | Cross | Easy | In the FY22 Q4 earnings call, management guided... | ## Summary   Management guided a total debt reduction of around ₹100 Crores for FY23. According t... | ## Summary In FY23, the actual change in total borrowings was an increase of ₹181.70 Crores, indi... | Base: ✅ / New: ❌ | 22.14s |
| **67** | Cross | Medium | The FY24 Chairman's letter describes business p... | ## Summary   The actual revenue growth for FY24 was 39.8%, and the PAT growth was 54.3% based on ... | I can only answer financial questions about the company corpus. Please ask about financials, annu... | Base: ✅ / New: ❌ | 27.2s |
| **72** | Cross | Hard | Management guided debt reduction as a priority ... | ## Summary   Despite management’s guidance prioritizing debt reduction and the Debt-Equity ratio ... | ## Summary Yes, debt did reduce in absolute terms from FY24 to FY25, with total borrowings decrea... | Base: ✅ / New: ❌ | 20.63s |

---

## Key Findings
1. **Severe Guardrail False-Positives**: GPT-4o-mini fails to interpret the safety instructions correctly in `rag.py`. It false-positive filters valid queries (**Q1, Q5, Q32, Q67**), blocking users with the standard refusal output: *"I can only answer financial questions about the company corpus..."*.
2. **Excel & Cross Routing Collapses**: GPT-4o-mini's capacity for complex, multi-hop routing completely broke down. Excel routing accuracy dropped to **0/3** (failing to identify standard sheet queries), and Cross-source routing also fell to **0/3**.
3. **Retrieval Degradation**: Due to poor query decomposition in the clarifier agent and incorrect routing, the Context Recall fell from **0.1956 to 0.1212**, leading to missed information.
4. **Latency & Cost Improvement**: GPT-4o-mini achieved a **35% cost reduction** ($0.0163 → $0.0106) and a **2.6x latency improvement** (24.28s → 9.25s). However, these efficiency gains are completely offset by the catastrophic quality regressions.

## Conclusion
**GPT-4.1-mini remains the production model.** 

While GPT-4o-mini offers appealing speed and cost metrics, it is currently not suitable for the complex instruction-following, safety guardrails, and agentic tool-calling tasks within FinBot's RAG pipeline. Standardizing on GPT-4o-mini would lead to critical feature failures.

## Raw Data References
* **GPT-4.1-mini (Baseline) JSON Report**: [eval_final_report_20260629_093114.json](file:///d:/FinBot/tests/results/eval_final_report_20260629_093114.json)
* **GPT-4o-mini JSON Report**: [eval_final_report_20260629_094123.json](file:///d:/FinBot/tests/results/eval_final_report_20260629_094123.json)
