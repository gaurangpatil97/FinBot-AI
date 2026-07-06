# FinBot Manual Grading Report (CRAFTSMAN AUTOMATION LTD)
## Run: run_001

This report presents the manual grading results for Craftsman Automation Ltd on benchmark `run_001`, evaluated using the exact same strict and lenient methodology as the Astral Ltd baseline.

### A) Overall Scores Table
| Metric | Count / Score | Percentage |
|---|---|---|
| Routing Accuracy | 33/100 | 33.00% |
| Answer Correctness (Strict) | 22/100 | 22.00% |
| Answer Correctness (Lenient) | 50/100 | 50.00% |

### B) By Section Table
| Section | Total Qs | Routing Accuracy % | Answer Correctness (Strict) % | Answer Correctness (Lenient) % |
|---|---|---|---|---|
| Excel | 20 | 40.0% | 45.0% | 65.0% |
| Ratio | 10 | 0.0% | 0.0% | 20.0% |
| PDF | 20 | 55.0% | 20.0% | 35.0% |
| Concall | 20 | 15.0% | 10.0% | 40.0% |
| Images | 10 | 30.0% | 10.0% | 70.0% |
| Cross-Source | 15 | 26.7% | 33.3% | 73.3% |
| Anomaly | 5 | 80.0% | 20.0% | 40.0% |

### C) By Difficulty Table
| Difficulty | Total Qs | Routing Accuracy % | Answer Correctness (Strict) % | Answer Correctness (Lenient) % |
|---|---|---|---|---|
| Easy | 11 | 27.3% | 36.4% | 81.8% |
| Medium | 58 | 31.0% | 15.5% | 31.0% |
| Hard | 31 | 38.7% | 29.0% | 74.2% |

### D) By Type Table
| Question Type | Total Qs | Routing Accuracy % | Answer Correctness (Strict) % | Answer Correctness (Lenient) % |
|---|---|---|---|---|
| Agnostic (40) | 40 | 22.5% | 7.5% | 22.5% |
| Company-Specific (60) | 60 | 40.0% | 31.7% | 68.3% |

## Critical Findings & Analysis

### 1. Severe Routing Failures on Ratio & Concall Sections
- **Ratio (0% Routing Accuracy):** The system failed to route a single question in the Ratio section to the correct Excel collection (`craftsman_automation_excel`). Instead, it routed to `craftsman_automation_pdf` or general collections, resulting in incomplete context and a **0% strict accuracy** score.
- **Concall (15% Routing Accuracy):** Concall routing was extremely low. The router consistently failed to search the earnings call transcripts, opting instead for PDF annual reports or Excel structured files, which starved the LLM of necessary management commentary.

### 2. Agnostic vs. Company-Specific Performance Discrepancy
- **Agnostic (7.5% Strict / 22.5% Lenient):** Agnostic questions scored very poorly. Because the agnostic questions were written with generic terms, the RAG system struggled to identify which Craftsman Automation sources were relevant, often failing to route or retrieve correctly. In contrast, **Company-Specific questions scored 31.7% Strict / 68.3% Lenient** because their specific references to Craftsman entities, plants, and metrics triggered much more precise retrieval.

### 3. Impact of Newly Added FY22 Q4 Concall Data (`crafts22Q4.pdf`) 
The addition of the FY22 Q4 earnings call transcript successfully resolved several historical data gaps:
- **Successful Questions:** Questions **CC5** (I&E segment YoY growth comparison), **CC7** (Daimler business risk discrepancy), and **CX1** (Debt reduction guidance vs actual balance sheet borrowings) succeeded for both Strict and Lenient grading because the system was able to retrieve `crafts22Q4.pdf`.
- **Partial Successes:** Questions **CC1**, **CC8**, and **CC9** succeeded for Lenient grading (achieving partially correct scores) due to elements extracted from the newly added transcript, though they missed some secondary details.

### 4. Comparison to Astral Ltd Baseline
- **Overall Lag:** Craftsman's overall metrics (**33% Routing, 22% Strict, 50% Lenient**) lag significantly behind Astral's baseline (**58% Routing, 30% Strict, 68% Lenient**). This is primarily driven by the catastrophic routing failures in the Ratio and Concall sections, confirming that Craftsman's collection metadata or query expansion mappings require significant optimization compared to the Astral baseline.

## Detailed Question-by-Question Grading

| ID | Section | Difficulty | Routing | Strict | Lenient | Notes / Reason for Failure |
|---|---|---|---|---|---|---|
| E1 | Excel | Medium | Incorrect | Incorrect | Partially Correct | Missing FY24 and FY26 revenue figures. |
| E2 | Excel | Medium | Incorrect | Incorrect | Partially Correct | Missing FY24 and FY26 net profit figures. |
| E3 | Excel | Medium | Incorrect | Correct | Correct | - |
| E4 | Excel | Medium | Incorrect | Incorrect | Incorrect | Used PBT instead of operating profit to calculate margins. |
| E5 | Excel | Medium | Incorrect | Correct | Correct | - |
| E6 | Excel | Medium | Incorrect | Incorrect | Incorrect | Calculated numbers instead of claiming the data is not available. |
| E7 | Excel | Medium | Incorrect | Incorrect | Incorrect | Claimed working capital metrics are not available, missing receivables/inventory data. |
| E8 | Excel | Medium | Incorrect | Incorrect | Incorrect | Stated incorrect periods and failed to calculate cumulative revenue growth. |
| E9 | Excel | Medium | Incorrect | Incorrect | Incorrect | Claimed EBITDA is not available in the context. |
| E10 | Excel | Medium | Incorrect | Incorrect | Incorrect | Calculated incorrect revenue CAGR and claimed total assets are not available. |
| R1 | Ratio | Medium | Incorrect | Incorrect | Partially Correct | Missed FY24 and FY26 debt-to-equity ratios. |
| R2 | Ratio | Medium | Incorrect | Incorrect | Incorrect | Calculated current ratio instead of stating it is not computable. |
| R3 | Ratio | Medium | Incorrect | Incorrect | Incorrect | Claimed net profit is not available, failing to calculate Return on Equity. |
| R4 | Ratio | Medium | Incorrect | Incorrect | Incorrect | Claimed Capital Employed is not available, failing to calculate ROCE. |
| R5 | Ratio | Medium | Incorrect | Incorrect | Incorrect | Calculated incorrect interest coverage ratios. |
| R6 | Ratio | Medium | Incorrect | Incorrect | Partially Correct | Missed total assets and shareholders' equity, failing to complete DuPont decomposition. |
| R7 | Ratio | Medium | Incorrect | Incorrect | Incorrect | Claimed all components are missing from context instead of identifying Trade Payables omission. |
| R8 | Ratio | Medium | Incorrect | Incorrect | Incorrect | Claimed net profit is not available and used PBT as proxy. |
| R9 | Ratio | Medium | Incorrect | Incorrect | Incorrect | Reported financial metrics for FY23 and FY24 instead of FY25 and FY26. |
| R10 | Ratio | Medium | Incorrect | Incorrect | Incorrect | Claimed required figures are missing and failed to calculate ROCE and cost of debt. |
| C1 | Concall | Medium | Incorrect | Incorrect | Incorrect | Stated outdated FY23 and FY24 drivers instead of FY26 guidance and priorities. |
| C2 | Concall | Medium | Correct | Incorrect | Incorrect | Missed Q4 FY25 performance drivers and specific segment revenues. |
| C3 | Concall | Medium | Correct | Incorrect | Incorrect | Missed specific FY26 risks regarding stationary engines and Sunbeam plant shift. |
| C4 | Concall | Medium | Correct | Incorrect | Incorrect | Claimed data is missing, failing to provide Craftsman segment guidance. |
| C5 | Concall | Medium | Incorrect | Incorrect | Incorrect | Stated slow-moving inventory provisions from FY23 instead of commodity price volatility details. |
| C6 | Concall | Medium | Incorrect | Incorrect | Incorrect | Stated capex from FY22 and claimed FY26 capex is missing. |
| C7 | Concall | Medium | Incorrect | Incorrect | Incorrect | Stated qualitative comments and outdated FY22 figures instead of specific FY26/FY27 additions. |
| C8 | Concall | Medium | Incorrect | Incorrect | Incorrect | Missed Fronberg Foundry, Sunbeam OCD, and DR Axion transaction values. |
| C9 | Concall | Medium | Incorrect | Incorrect | Incorrect | Stated outdated segment metrics instead of Q3 and Q4 FY25 EBIT impacts. |
| C10 | Concall | Medium | Incorrect | Incorrect | Partially Correct | Missed consolidated net debt, debt-to-EBITDA targets, and Q4 FY25 projections. |
| P1 | PDF | Medium | Incorrect | Incorrect | Incorrect | Reported segment revenues for FY23 vs FY22 instead of FY25 vs FY24. |
| P2 | PDF | Medium | Correct | Correct | Correct | - |
| P3 | PDF | Medium | Correct | Incorrect | Incorrect | Reported related party transactions and KMP remuneration for FY23 instead of FY25 vs FY24. |
| P4 | PDF | Medium | Incorrect | Incorrect | Incorrect | Claimed contingent liabilities data is missing from context. |
| P5 | PDF | Medium | Correct | Incorrect | Partially Correct | Missed key strategic acquisitions (Fronberg, DR Axion, Sunbeam) and capital commitment values. |
| P6 | PDF | Medium | Correct | Incorrect | Incorrect | Stated derivative accounting as Key Audit Matter instead of PPE and Business Combinations. |
| P7 | PDF | Medium | Incorrect | Incorrect | Incorrect | Reported segment profits for wrong years (FY23 vs FY22) and claimed FY25 assets/liabilities are missing. |
| P8 | PDF | Medium | Incorrect | Incorrect | Incorrect | Claimed Other Expenses breakdown is missing from context. |
| P9 | PDF | Medium | Correct | Incorrect | Incorrect | Stated outdated FY24 standard amendments instead of FY25 status. |
| P10 | PDF | Medium | Correct | Incorrect | Incorrect | Reported outdated details and missed exact FY25 provisions break-up. |
| CE1 | Excel | Easy | Correct | Correct | Correct | - |
| CE2 | Excel | Easy | Correct | Correct | Correct | - |
| CE3 | Excel | Medium | Correct | Correct | Correct | - |
| CE4 | Excel | Medium | Correct | Incorrect | Incorrect | Calculated incorrect margins (10.13% and 5.12% vs expected 19.74% and 14.64%). |
| CE5 | Excel | Medium | Correct | Correct | Correct | - |
| CE6 | Excel | Hard | Incorrect | Incorrect | Partially Correct | Missed expected OPM compression figures but captured other P&L drivers and audit implications. |
| CE7 | Excel | Hard | Correct | Correct | Correct | - |
| CE8 | Excel | Hard | Incorrect | Incorrect | Partially Correct | Missed calculating the inventory days (96 days in FY23 and 79 days in FY26) to assess efficiency. |
| CE9 | Excel | Hard | Correct | Correct | Correct | - |
| CE10 | Excel | Hard | Correct | Correct | Correct | - |
| CP1 | PDF | Easy | Incorrect | Incorrect | Incorrect | Reported incorrect consideration of ₹1,200 Cr instead of ₹375 Cr for DR Axion. |
| CP2 | PDF | Easy | Incorrect | Correct | Correct | - |
| CP3 | PDF | Medium | Correct | Incorrect | Incorrect | Reported ROE (+33%) as highest change instead of Interest Coverage Ratio (+53%). |
| CP4 | PDF | Medium | Incorrect | Incorrect | Incorrect | Stated incorrect ratio values and identified Net Profit Margin instead of Return on Net Worth. |
| CP5 | PDF | Medium | Incorrect | Incorrect | Incorrect | Claimed the magnitudes of the changes are missing from the context. |
| CP6 | PDF | Hard | Correct | Incorrect | Partially Correct | Missed the specific base-period consolidation timing asymmetry (2 months vs 12 months) that distorts growth optics. |
| CP7 | PDF | Hard | Correct | Incorrect | Partially Correct | Missed the specific 0% to 100% related party loan concentration jump. |
| CP8 | PDF | Hard | Correct | Correct | Correct | - |
| CP9 | PDF | Hard | Correct | Incorrect | Incorrect | Stated business combinations as the sole Standalone KAM instead of PPE, and failed to identify the omission of acquisitions as a KAM. |
| CP10 | PDF | Hard | Incorrect | Correct | Correct | - |
| CC1 | Concall | Easy | Incorrect | Incorrect | Partially Correct | Missed the revised full-year capex figure of ₹275 Cr. |
| CC2 | Concall | Easy | Incorrect | Incorrect | Incorrect | Stated incorrect actual Q1 FY23 revenue of ₹600 Cr instead of ₹676 Cr. |
| CC3 | Concall | Medium | Incorrect | Incorrect | Correct | Missed the specific ₹78 Cr / ₹10 Cr normalization details. |
| CC4 | Concall | Medium | Incorrect | Incorrect | Incorrect | Missed the aluminium business order and the ₹70 Cr unplanned capex reason. |
| CC5 | Concall | Medium | Incorrect | Correct | Correct | - |
| CC6 | Concall | Hard | Incorrect | Incorrect | Correct | Concluded structural margin pressure instead of timing/inventory effect of 8-10 weeks. |
| CC7 | Concall | Hard | Incorrect | Correct | Correct | - |
| CC8 | Concall | Hard | Incorrect | Incorrect | Partially Correct | Missed the Q3 FY22 one-off release of ₹7 Cr. |
| CC9 | Concall | Hard | Incorrect | Incorrect | Partially Correct | Missed the original FY22 starting debt base of ₹713 Cr. |
| CC10 | Concall | Hard | Incorrect | Incorrect | Incorrect | Reported incorrect actual revenue of ₹563.5 Cr, claiming a shortfall instead of a beat. |
| CI1 | Images | Easy | Incorrect | Incorrect | Correct | Missed the historical FY04 export comparison detail. |
| CI2 | Images | Easy | Correct | Incorrect | Correct | Missed the remaining segment shares (Aluminium 25% and I&E 24%). |
| CI3 | Images | Medium | Incorrect | Incorrect | Incorrect | Stated incorrect direction for Debt-Equity ratio (said it increased instead of improved/decreased). |
| CI4 | Images | Medium | Correct | Incorrect | Incorrect | Stated peak was in FY23 instead of FY19, missing the full 5-year trend. |
| CI5 | Images | Medium | Correct | Incorrect | Correct | Missed the specific growth percentages for FY21. |
| CI6 | Images | Hard | Incorrect | Incorrect | Partially Correct | Missed the 5-year Debt-EBITDA trend and rising leverage details. |
| CI7 | Images | Hard | Incorrect | Correct | Correct | - |
| CI8 | Images | Hard | Incorrect | Incorrect | Partially Correct | Missed specific DR Axion turnover (₹1,246 Cr) and intercompany elimination (₹9 Cr) reconciliation. |
| CI9 | Images | Hard | Incorrect | Incorrect | Correct | Missed the net deficit of ₹507 Cr and German subsidiary risk. |
| CI10 | Images | Hard | Incorrect | Incorrect | Incorrect | Missed the 'Excluding Excise Duty' GST base effect caveat. |
| CX1 | Cross-Source | Easy | Incorrect | Correct | Correct | - |
| CX2 | Cross-Source | Easy | Incorrect | Incorrect | Partially Correct | Stated incorrect Interest figures and failed to confirm the MD&A's interest coverage ratio. |
| CX3 | Cross-Source | Easy | Incorrect | Incorrect | Partially Correct | Used incorrect EBITDA and derived debt figures, missing the net debt explanation. |
| CX4 | Cross-Source | Medium | Incorrect | Correct | Correct | - |
| CX5 | Cross-Source | Medium | Incorrect | Correct | Correct | - |
| CX6 | Cross-Source | Medium | Correct | Correct | Correct | - |
| CX7 | Cross-Source | Medium | Incorrect | Incorrect | Partially Correct | Missed the DR Axion turnover (₹1,246 Cr) and intercompany elimination (₹9 Cr) reconciliation. |
| CX8 | Cross-Source | Hard | Incorrect | Incorrect | Partially Correct | Missed the specific ₹856 Cr actual capex and 3x underguidance details for FY23. |
| CX9 | Cross-Source | Hard | Incorrect | Incorrect | Incorrect | Used incorrect Net Worth and calculated incorrect RoNW (2.73% vs expected 6.8%). |
| CX10 | Cross-Source | Hard | Correct | Correct | Correct | - |
| CX11 | Cross-Source | Hard | Incorrect | Incorrect | Incorrect | Claimed EBITDA is missing, failing to calculate Debt-to-EBITDA for FY25. |
| CX12 | Cross-Source | Hard | Correct | Incorrect | Incorrect | Confused forex hedges with commodity hedges, claiming aluminum price risk is hedged. |
| CX13 | Cross-Source | Hard | Correct | Incorrect | Partially Correct | Claimed FY22 segment EBIT is missing and estimated incorrect percentage share. |
| CX14 | Cross-Source | Hard | Incorrect | Incorrect | Incorrect | Claimed loans to related parties are missing from Excel balance sheet. |
| CX15 | Cross-Source | Hard | Incorrect | Incorrect | Correct | Missed specific visual and QIP ratio details but captured the core debt accumulation contradiction. |
| CA1 | Anomaly | Medium | Correct | Incorrect | Incorrect | Calculated Capex using investing cash flow proxy instead of stating it is not available. |
| CA2 | Anomaly | Medium | Correct | Incorrect | Incorrect | Calculated current ratio using assumptions instead of stating it is not computable. |
| CA3 | Anomaly | Hard | Correct | Incorrect | Incorrect | Claimed Inventory and Receivable days are missing while fabricating Payable days. |
| CA4 | Anomaly | Hard | Incorrect | Correct | Correct | - |
| CA5 | Anomaly | Hard | Correct | Incorrect | Partially Correct | Calculated proxy FCF instead of identifying it is not computable, but correctly flagged missing Market Cap. |