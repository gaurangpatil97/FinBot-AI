"""
FinBot Evaluation Script — run_eval.py
Fires all 77 evaluation questions at the FinBot API and saves raw results.

Usage:
    python run_eval.py

Output:
    tests/results/eval_raw_results.json
    tests/results/eval_raw_results.txt

After running:
    1. Open eval_raw_results.json
    2. For each question, add "correct": true/false based on your manual review
    3. Run score_eval.py to get full metrics
"""

import json
import time
import requests
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000/api/v1/query"
COMPANY_SLUG = "craftsman_automation_ltd"
RESULTS_DIR = Path("tests/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
JSON_OUTPUT = RESULTS_DIR / f"eval_raw_results_{TIMESTAMP}.json"
TXT_OUTPUT  = RESULTS_DIR / f"eval_raw_results_{TIMESTAMP}.txt"

# ── Question Bank ─────────────────────────────────────────────────────────────
QUESTIONS = [

    # ── EXCEL (15) ────────────────────────────────────────────────────────────
    {
        "id": 1,
        "section": "Excel",
        "difficulty": "Easy",
        "question": "What was the Net Profit reported by the company in FY26?",
        "expected_answer": "Net Profit in FY26 was ₹383.99 Cr — a recovery from ₹194.57 Cr in FY25 and the highest absolute net profit in the 10-year dataset.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 2,
        "section": "Excel",
        "difficulty": "Easy",
        "question": "What were total Borrowings on the Balance Sheet as at end of FY24?",
        "expected_answer": "Total Borrowings as at 31 March 2024 were ₹1,754.82 Cr, up from ₹1,240.23 Cr in FY23 — an increase of ₹514.59 Cr.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 3,
        "section": "Excel",
        "difficulty": "Easy",
        "question": "What was the Cash from Operating Activity in FY23?",
        "expected_answer": "Cash from Operating Activity in FY23 was ₹607.66 Cr — the highest among all 10 years in the dataset.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 4,
        "section": "Excel",
        "difficulty": "Easy",
        "question": "What was the Depreciation charge for the company in FY22?",
        "expected_answer": "Depreciation in FY22 was ₹205.99 Cr, compared to ₹192.45 Cr in FY21 — a modest 7% increase.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 5,
        "section": "Excel",
        "difficulty": "Medium",
        "question": "Calculate the Operating Profit Margin for FY24 and FY25 and comment on the trend. OPM = Operating Profit / Sales × 100",
        "expected_answer": "FY24 OPM: 19.74%. FY25 OPM: 14.64%. OPM contracted sharply by ~510 bps despite 27.8% revenue growth — a significant margin deterioration.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 6,
        "section": "Excel",
        "difficulty": "Medium",
        "question": "Compute the Debt-to-Equity ratio for FY25 and FY26 and assess the change in financial leverage.",
        "expected_answer": "FY25 D/E = 0.83x. FY26 D/E = 1.11x. Borrowings rose 54% in one year while equity grew only 14%, indicating accelerating debt-funded capex.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 7,
        "section": "Excel",
        "difficulty": "Medium",
        "question": "Calculate Debtor Days for FY23 and FY26 and compare receivable collection efficiency. Debtor Days = Receivables / Sales × 365",
        "expected_answer": "FY23: 61.4 days. FY26: 50.2 days. Receivables grew 4.6x but Debtor Days improved from 61 to 50 days — a positive working capital signal.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 8,
        "section": "Excel",
        "difficulty": "Medium",
        "question": "Compute the Interest Coverage Ratio for FY22 and FY25 and evaluate debt serviceability. ICR = Operating Profit / Interest",
        "expected_answer": "FY22 ICR: 6.34x. FY25 ICR: 3.85x. ICR has deteriorated significantly as debt servicing costs outpaced operating profit growth.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 9,
        "section": "Excel",
        "difficulty": "Hard",
        "question": "In FY25, sales grew 27.8% YoY yet PBT fell 39.4% from FY24. Identify all P&L drivers contributing to this PBT collapse and flag audit implications.",
        "expected_answer": "Key drivers: OPM contracted from 19.74% to 14.64%; Interest rose from ₹174.54 Cr to ₹216.64 Cr; Other Income collapsed from ₹18.09 Cr to ₹0.30 Cr; Depreciation rose by ₹69.33 Cr. Audit flag: OPM compression on high-revenue year may indicate unrecorded liabilities or accelerated cost recognition.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 10,
        "section": "Excel",
        "difficulty": "Hard",
        "question": "Assess the Operating Cash Flow quality for FY25 and FY26 by computing OCF-to-Net-Profit ratio. Is the company's profit of high quality?",
        "expected_answer": "OCF/NP: FY24: 1.69x, FY25: 1.46x, FY26: 1.36x. The ratio has declined persistently — profit quality is deteriorating. Earnings are increasingly accrual-based.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 11,
        "section": "Excel",
        "difficulty": "Hard",
        "question": "The company shows a negative effective tax rate in FY17 where Net Profit exceeded PBT. Explain the mechanics and flag forensic concerns.",
        "expected_answer": "FY17: PBT = ₹36.67 Cr; Tax = −₹43.07 Cr; Net Profit = ₹79.74 Cr. Effective tax rate = −117.5%. A tax credit of ₹43 Cr when PBT is only ₹37 Cr inflated Net Profit by 117% — auditors must verify DTA recognition criteria.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 12,
        "section": "Excel",
        "difficulty": "Hard",
        "question": "Evaluate the capex intensity trend from FY23 to FY26 against OCF. Is the company's capex program self-funded or debt-reliant?",
        "expected_answer": "OCF coverage of capex: FY23: 71%, FY24: 64%, FY25: 17%, FY26: 35%. The company is clearly NOT self-funding capex. Borrowings grew from ₹1,240 Cr (FY23) to ₹3,623 Cr (FY26).",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 13,
        "section": "Excel",
        "difficulty": "Hard",
        "question": "In FY26, Other Expenses in the P&L is reported at ₹1,842.44 Cr — more than 5x the prior year figure of ₹18.98 Cr in FY25. Flag this anomaly and its implications.",
        "expected_answer": "FY26 Other Expenses: ₹1,842.44 Cr — a 9,603% increase. This is likely a data reclassification anomaly. Cost structure analysis cannot be performed at sub-line level for FY26.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 14,
        "section": "Excel",
        "difficulty": "Hard",
        "question": "The company paid zero dividend in FY20 and FY21 despite reporting net profits. Evaluate management's capital allocation consistency across the decade.",
        "expected_answer": "FY20 dividend skip is explainable (COVID, revenue fell 18%). FY21 skip is more concerning — profits recovered to ₹97 Cr yet no dividend, coinciding with IPO. Post-IPO dividends resumed and scaled. Payout ratios remain low (5-10%), consistent with growth-capex-heavy phase.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },
    {
        "id": 15,
        "section": "Excel",
        "difficulty": "Hard",
        "question": "Inventory grew from ₹836 Cr in FY23 to ₹1,745 Cr in FY26 — a 109% increase while sales grew 153%. Analyse inventory efficiency and flag any buildup risk.",
        "expected_answer": "Inventory days improved from 96 days (FY23) to 79 days (FY26) despite absolute inventory doubling. No buildup risk based on disclosed figures. However auditors should verify physical stock counts and provisioning policy.",
        "expected_source": ["excel"],
        "expected_citation_contains": ["Craftsman Auto.xlsx"],
    },

    # ── CONCALL (15) ──────────────────────────────────────────────────────────
    {
        "id": 16,
        "section": "Concall",
        "difficulty": "Easy",
        "question": "What was the total consolidated H1 FY23 revenue reported by the company, and by what percentage did it exceed H1 FY22?",
        "expected_answer": "H1 FY23 revenue was ₹1,447 crores, compared to ₹1,000 crores in H1 FY22 — a 44.7% increase.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 17,
        "section": "Concall",
        "difficulty": "Easy",
        "question": "What was the credit rating of the company at the time of the FY23 Q1 earnings call, and what was it upgraded from?",
        "expected_answer": "The rating was upgraded to A+ with stable outlook, from A with stable outlook, as disclosed during the Q1 FY23 earnings call.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 18,
        "section": "Concall",
        "difficulty": "Easy",
        "question": "What was the segment-wise EBIT for the Auto Powertrain, Aluminum Products, and Industrial & Engineering divisions in FY23 Q1?",
        "expected_answer": "Auto Powertrain: ₹95 crores; Aluminum Products: ₹20 crores; Industrial & Engineering: ₹11 crores. Total EBIT: ₹112 crores.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 19,
        "section": "Concall",
        "difficulty": "Easy",
        "question": "What was the total debt of the company as of end of FY22 Q4, and how was it split between long-term and working capital loans?",
        "expected_answer": "Total debt as of March 2022 stood at ₹713 crores — long-term debt ₹522 crores and working capital loans ₹193 crores.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 20,
        "section": "Concall",
        "difficulty": "Medium",
        "question": "Calculate the Debt-to-EBITDA ratio for FY23 H1 as disclosed by management, and compare it to the prior full-year ratio. What does the trend indicate?",
        "expected_answer": "H1 FY23 Debt-to-EBITDA (annualised) = 1.08x, compared to 1.33x for full-year FY22. Trend indicates improving debt serviceability as EBITDA grew 31% YoY.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 21,
        "section": "Concall",
        "difficulty": "Medium",
        "question": "For FY23 Q2, management disclosed that aluminum prices fell approximately 10% QoQ but claimed operational margins were in line with Q1. Is this numerically consistent with the value addition numbers disclosed?",
        "expected_answer": "Value addition dropped from ₹71 Cr (Q1) to ₹68 Cr (Q2). Management's normalisation claim: without price drop, value addition would have been ₹78 Cr. The ₹10 Cr gap is consistent with their 10% price drop claim.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 22,
        "section": "Concall",
        "difficulty": "Medium",
        "question": "Compare the value addition for the Industrial & Engineering segment in FY23 Q2 with the same quarter of the prior year. What is the YoY growth rate?",
        "expected_answer": "I&E value addition in Q2 FY23 = ₹76 crores vs Q2 FY22 = ₹42 crores — a YoY growth of ~81%. Value addition growing faster than revenue implies improvement in sales mix quality.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 23,
        "section": "Concall",
        "difficulty": "Medium",
        "question": "The company revised its full-year FY23 CAPEX guidance upward from ₹225 crores to ₹275 crores. Identify the specific reason for the revision.",
        "expected_answer": "An unplanned additional CAPEX of ~₹70 crores was triggered by a sizable aluminium business order received in April 2022, where the customer required production to start by Q4 FY23.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 24,
        "section": "Concall",
        "difficulty": "Hard",
        "question": "Management claimed in FY23 Q1 that the company's annualised pre-tax ROCE was 26%, an improvement from 20% for the full prior year. However total debt increased by ₹50 crores QoQ. Identify and explain the apparent contradiction.",
        "expected_answer": "ROCE improved because EBIT grew and the company took cash discounts from creditors (enabled by credit rating upgrade), reducing net capital employed even as gross debt rose. The rise in short-term debt was working capital-driven, not capex-driven.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 25,
        "section": "Concall",
        "difficulty": "Hard",
        "question": "Management stated during FY23 Q1 that bonus provision was front-loaded to Q1. Identify all staff cost one-offs disclosed across Q1 FY23 and Q3 FY22 calls, and assess the risk that normalised staff costs are being underestimated.",
        "expected_answer": "Q3 FY22: bonus release of ~₹7 crores as one-off. Q1 FY23: bonus provision made early along with salary increases. The pattern reveals bonus recognition is being shifted between quarters — creating risk of distorted inter-quarter EBITDA comparisons.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 26,
        "section": "Concall",
        "difficulty": "Hard",
        "question": "The company merged its Auto Aluminum and Industrial Aluminum sub-segments into a single Aluminum Products segment effective FY23 Q1. What financial reporting impact did this restructuring have?",
        "expected_answer": "The restructuring makes direct YoY comparison unreliable without restatement. EBIT for Industrial & Engineering dropped dramatically which management attributed to product mix but could partly reflect removal of higher-margin aluminum sub-segments.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 27,
        "section": "Concall",
        "difficulty": "Hard",
        "question": "Management guided in FY22 Q4 for a ₹100 crore debt reduction in FY23. By FY23 Q2, total debt was ~₹720 crores. Verify whether the original guidance is still achievable and quantify the gap.",
        "expected_answer": "Original guidance: debt reduction from ₹713 Cr to ~₹613 Cr. Q2 FY23 actual: ~₹720 Cr. Gap vs original guidance: ~₹107 crores. Management's explanation evolved from working capital driven to debt is under control.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 28,
        "section": "Concall",
        "difficulty": "Hard",
        "question": "Management claimed in FY23 Q2 that Aluminum Products segment margins were in line with Q1 despite a drop in reported EBIT. Verify this claim using value addition data and assess whether there is an unacknowledged structural margin issue.",
        "expected_answer": "VA margin deteriorated from 41.5% (Q1) to 34.7% (Q2) despite revenue increase. Management's explanation is plausible but not fully verifiable — the actual inventory holding cost vs replacement cost difference was never quantified precisely.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 29,
        "section": "Concall",
        "difficulty": "Hard",
        "question": "Management guided revenue of ₹600 crores for FY23 Q1 in the FY22 Q4 call. What did the actual Q1 FY23 numbers show and what does the gap imply?",
        "expected_answer": "Actual Q1 FY23 revenue = ₹676 crores, exceeding guidance by ~12.7%. Consistently conservative guidance followed by beats can indicate managed earnings narrative or sandbagging for investor optics.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },
    {
        "id": 30,
        "section": "Concall",
        "difficulty": "Hard",
        "question": "Across the FY22 Q3 and Q4 earnings calls, management made specific claims about the Daimler business risk stating only 8-9% impact by FY27-28. By Q1 FY23, a different number emerged — 15% of the Daimler portfolio by 2024. Identify the discrepancy.",
        "expected_answer": "The disclosed impact shifted from 8-9% of Daimler value addition eventually (Q4 FY22) to 15% of Daimler portfolio by FY24 (Q1 FY23) — a meaningful escalation. The inconsistency between calls on the percentage at risk is a forensic flag for adequacy of risk disclosures.",
        "expected_source": ["concall"],
        "expected_citation_contains": ["CraftsmanAutomation"],
    },

    # ── PDF TEXT (16) ─────────────────────────────────────────────────────────
    {
        "id": 31,
        "section": "PDF",
        "difficulty": "Easy",
        "question": "What specific operating model does the company's Chairman describe as its unique competitive differentiator in the Chairman's letter for FY22?",
        "expected_answer": "The Chairman describes a Company-within-Company model — all verticals run as independent profit-making enterprises while sharing common philosophies, best-practices, and facilities.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 32,
        "section": "PDF",
        "difficulty": "Medium",
        "question": "In the company's FY22 MD&A, which specific financial ratio showed the highest year-on-year percentage change, and what two factors does management explicitly attribute to this change?",
        "expected_answer": "The Interest Coverage Ratio showed the highest change at +53% (from 4.17x in FY21 to 6.40x in FY22). Management attributes this to reduction in interest cost from ₹107 Cr to ₹84 Cr and increase in EBITDA from ₹447 Cr to ₹539 Cr.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 33,
        "section": "PDF",
        "difficulty": "Hard",
        "question": "The company's FY22 auditor identified two Key Audit Matters. What are they, and for the derivative contracts KAM, what is the combined carrying value of derivative assets and liabilities?",
        "expected_answer": "Two KAMs: (1) Accounting for Derivative Contracts — derivative assets ₹855 Lakhs, liabilities ₹538 Lakhs. (2) Accounting for PPE. Hedge effectiveness testing requires an auditor's expert.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 34,
        "section": "PDF",
        "difficulty": "Hard",
        "question": "In the company's FY22 Directors' Report under Risk Management, what is the stated mitigation strategy against Funding Risk, and does the metric cited match the MD&A Key Ratios table?",
        "expected_answer": "Mitigation strategy cites debt-equity ratio of 0.63x and net cash from operations of ₹322 Cr. MD&A independently reports Debt Equity Ratio as 0.63x for FY22 — confirming numerical consistency.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 35,
        "section": "PDF",
        "difficulty": "Easy",
        "question": "What was the key inorganic highlight that the company disclosed in FY23, and what was the total consideration paid?",
        "expected_answer": "Craftsman acquired a controlling stake (76%) in DR Axion India Private Limited in February 2023. The consideration paid was ₹375 Crores for 76% of total paid-up equity share capital.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 36,
        "section": "PDF",
        "difficulty": "Medium",
        "question": "According to the MD&A of the company for FY23, what was the stated reason for the decline in the Interest Coverage Ratio, and what does this imply about financing risk?",
        "expected_answer": "ICR declined from 6.40x to 5.74x due to increase in interest cost from ₹84 Cr to ₹117 Cr — primarily driven by higher borrowings to fund the DR Axion acquisition.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 37,
        "section": "PDF",
        "difficulty": "Hard",
        "question": "The Directors' Report of the company for FY23 states all RPTs were on arm's length basis. However the Risk Management Committee is chaired by the Chairman & Managing Director himself. What governance anomaly does this present?",
        "expected_answer": "The person with the largest economic interest in related-party dealings chairs the body responsible for monitoring enterprise-wide risk. SEBI LODR Regulation 21 mandates an Independent Director should chair the Risk Management Committee at listed entities.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 38,
        "section": "PDF",
        "difficulty": "Hard",
        "question": "The Statutory Auditor identified two Key Audit Matters in the standalone audit of the company for FY23. For the derivative KAM, what is the carrying value of derivative assets and liabilities as at 31 March 2023, and does the auditor qualify the opinion?",
        "expected_answer": "Derivative assets: ₹936 Lakhs, liabilities: ₹375 Lakhs (net asset ₹561 Lakhs). The audit opinion is unqualified — no Emphasis of Matter on hedge accounting. The KAM itself signals elevated audit effort in this area.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 39,
        "section": "PDF",
        "difficulty": "Easy",
        "question": "What were the two Key Audit Matters identified by the statutory auditors of the company for FY24, and what percentage of total assets does PPE represent?",
        "expected_answer": "Two KAMs: (1) Accounting for derivative contracts — derivative assets ₹943 Lakhs, liabilities ₹259 Lakhs. (2) Accounting for PPE. PPE including CWIP represents 48% of total assets.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 40,
        "section": "PDF",
        "difficulty": "Medium",
        "question": "According to the MD&A of the company for FY24, what are the specific reasons cited for the deterioration in the Interest Coverage Ratio and the Debt-Equity Ratio, and what is the magnitude of each change?",
        "expected_answer": "ICR deteriorated 26% from 5.74x to 4.24x due to increase in interest cost from ₹117 Cr to ₹155 Cr. Debt-Equity Ratio deteriorated 26% from 0.72x to 0.91x due to increase in borrowings.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 41,
        "section": "PDF",
        "difficulty": "Hard",
        "question": "The Chairman's letter for FY24 describes a consolidation and moderation in growth. Cross-referencing MD&A segment-wise data, which segment experienced the sharpest EBIT margin compression and by how much?",
        "expected_answer": "Automotive Powertrain experienced the sharpest compression — EBIT margin fell from 25% to 19%, a compression of 600 basis points. The Chairman's moderation characterisation omits this Powertrain deterioration.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 42,
        "section": "PDF",
        "difficulty": "Hard",
        "question": "The company's Board Report for FY24 states all RPTs were arm's length and DR Axion posted turnover of ₹1,246 Cr in FY24. What forensic risk does the short acquisition history and consolidation timing create?",
        "expected_answer": "DR Axion was acquired on 1 February 2023 — only 2 months consolidated in FY23. In FY24 it contributed a full year of ₹1,246 Cr revenue. This base-period asymmetry inflates consolidated growth optics. Intra-group transactions must be verified for arm's length pricing.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 43,
        "section": "PDF",
        "difficulty": "Easy",
        "question": "What is the credit rating assigned to the company's long-term and short-term loan facilities as affirmed during FY25?",
        "expected_answer": "CRISIL reaffirmed long-term loan facilities as AA-/Stable and short-term loan facilities as A1+.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 44,
        "section": "PDF",
        "difficulty": "Medium",
        "question": "According to the FY25 MD&A, what was management's stated explanation for the significant deterioration in Operating Profit Margin, Net Profit Margin, and Return on Net Worth, and which ratio deteriorated most severely?",
        "expected_answer": "Management attributed deterioration to one-time expenses for acquisitions and initial losses on greenfield projects. Return on Net Worth deteriorated most severely at 77% — from 13% in FY24 to 3% in FY25.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 45,
        "section": "PDF",
        "difficulty": "Hard",
        "question": "The company's FY25 Directors' Report states all RPTs were arm's length. However what does the BRSR data reveal about the concentration of loans and advances with related parties in FY25?",
        "expected_answer": "BRSR discloses loans and advances to related parties jumped from 0% to 100% of total loans and advances in one year. This complete shift warrants forensic examination of whether loans are to subsidiaries or represent undisclosed related-party financial exposure.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 46,
        "section": "PDF",
        "difficulty": "Hard",
        "question": "The Statutory Auditors identified only one KAM in the standalone audit for FY25. What was it, and does the absence of a KAM on the three acquisitions exceeding ₹740 Crores represent a gap?",
        "expected_answer": "The sole KAM is Accounting for PPE (44% of total assets). The auditors did not designate the acquisitions as KAMs despite high-risk, high-judgement events involving goodwill recognition and fair value assessments. This is an audit quality concern.",
        "expected_source": ["pdf"],
        "expected_citation_contains": ["Annual-Report"],
    },

    # ── IMAGES (16) ───────────────────────────────────────────────────────────
    {
        "id": 47,
        "section": "Images",
        "difficulty": "Easy",
        "question": "In the About the company infographic page of the FY22 annual report, a donut chart shows the revenue split by business segment. What are the three business segments shown and their respective percentage contributions?",
        "expected_answer": "Automotive Powertrain: 52%, Industrial & Engineering: 28%, Automotive Aluminium: 20%.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 48,
        "section": "Images",
        "difficulty": "Easy",
        "question": "In the Key Performance Indicators section of the FY22 annual report, bar charts track Net Profit across five financial years FY18 to FY22. What were the Net Profit values in FY20 and FY21?",
        "expected_answer": "FY20 Net Profit: ₹37 Crores. FY21 Net Profit: ₹97 Crores. The bar chart shows a steep recovery from the COVID-impacted FY20 trough.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 49,
        "section": "Images",
        "difficulty": "Medium",
        "question": "In the KPI Position section bar charts of the FY22 annual report, what is the trend in the Debt/EBITDA ratio over the five-year period shown FY18 to FY22?",
        "expected_answer": "FY18: 2.92x, FY19: 2.57x, FY20: 2.31x, FY21: 1.57x, FY22: 1.33x. Consistent downward improving trend — FY22 at 1.33x is the lowest in the five-year series.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 50,
        "section": "Images",
        "difficulty": "Hard",
        "question": "In the FY22 annual report, opening pages contain CAGR infographics showing growth from FY18 to FY22 across Revenue, EBIT, EBITDA, and PAT. The PAT CAGR of 49% is significantly higher than Revenue CAGR of 11%. What specific caveat is noted on the Revenue CAGR infographic that a CA must flag?",
        "expected_answer": "A footnote reads Excluding Excise Duty — the FY18 base figure excludes the pre-GST excise duty component, making the revenue CAGR comparison potentially understated. This means the PAT outperformance must be interpreted with this base effect in mind.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 51,
        "section": "Images",
        "difficulty": "Easy",
        "question": "The Revenue mix across sectors FY23 donut chart on the An Edge above the rest visual page shows three business segments. What percentage does the Automotive Powertrain segment contribute to total revenue?",
        "expected_answer": "Automotive Powertrain contributes 51% of total revenue. Remaining segments: Aluminium Products at 25% and Industrial & Engineering at 24%.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 52,
        "section": "Images",
        "difficulty": "Easy",
        "question": "The Revenue mix across geographies FY23 donut chart in the annual report shows a domestic vs export split. What percentage of revenue is domestic?",
        "expected_answer": "92% domestic revenue and 8% export revenue. In FY04, over 80% of revenues came from exports — a near-complete reversal of geographic mix over ~19 years.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 53,
        "section": "Images",
        "difficulty": "Medium",
        "question": "In the Over the years financial performance multi-year bar chart section of the FY23 annual report, the Debt-equity Ratio chart shows values across FY19 to FY23. In which year did the ratio peak and what was the peak value?",
        "expected_answer": "The ratio peaked in FY19 at 1.42x. The five-year trend shows consistent de-leveraging from 1.42x (FY19) to 0.63x (FY22), with a slight uptick to 0.72x in FY23 reflecting additional debt for the DR Axion acquisition.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 54,
        "section": "Images",
        "difficulty": "Hard",
        "question": "In the Over the years bar chart section of the FY23 annual report, the Debt-EBITDA Ratio chart shows a value for FY21 that appears anomalous relative to surrounding years. What does cross-reading against the Net Profit bar chart reveal?",
        "expected_answer": "FY21 Debt-EBITDA ~1.57x but Net Profit shows ~₹37 Cr — a dramatic collapse. The combination of low net profit with moderate Debt-EBITDA confirms FY21 was a severe pandemic-impact year with high depreciation and finance cost load.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 55,
        "section": "Images",
        "difficulty": "Easy",
        "question": "In the donut chart labelled Revenue by Geography Consolidated Basis in the FY24 annual report, what percentage of total consolidated revenue of ₹4,452 Crore is derived from domestic sales versus exports?",
        "expected_answer": "Domestic: ₹4,254 Crore = 96% of total consolidated revenue. Exports: ₹198 Crore = 4%.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 56,
        "section": "Images",
        "difficulty": "Medium",
        "question": "In the five-year bar charts under Performance Consolidated Basis on the KPI page of the FY24 annual report, compare the trajectory of Net Profit versus EBITDA from FY20 to FY24. In which year did Net Profit grow proportionally fastest?",
        "expected_answer": "FY21 shows the most disproportionate Net Profit growth (₹40 Cr to ₹97 Cr = ~143% jump) vs EBITDA growth (~10%), suggesting significant below-EBITDA line improvement from lower finance costs or tax benefits.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 57,
        "section": "Images",
        "difficulty": "Hard",
        "question": "In the Revenue by Business Consolidated Basis donut chart in the FY24 annual report, the Aluminium Products segment shows ₹2,154 Crore (48%) of consolidated revenue. However the MD&A segment table reports Aluminium standalone sales of only ₹917 Crore. What accounts for the ₹1,237 Crore discrepancy?",
        "expected_answer": "The discrepancy reconciles with DR Axion India's standalone FY24 turnover of ₹1,246 Crore. The donut chart uses consolidated segment revenue including DR Axion while MD&A discloses only standalone figures — a transparency gap not flagged on the chart itself.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 58,
        "section": "Images",
        "difficulty": "Hard",
        "question": "In the Position section bar charts on the FY24 KPI page, the Debt-Equity Ratio bar chart shows 0.88x for FY24 yet the standalone MD&A reports 0.91x. What is the likely source of this discrepancy and what does the five-year Debt-EBITDA trend reveal?",
        "expected_answer": "Discrepancy: bar chart uses consolidated basis (higher equity from DR Axion) while MD&A reports standalone. Debt-EBITDA trend: FY20 2.56x → FY21 1.57x → FY22 1.32x → FY23 1.65x → FY24 1.72x. Leverage has been rising for two consecutive years contradicting Chairman's debt reduction narrative.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 59,
        "section": "Images",
        "difficulty": "Easy",
        "question": "The segment-wise performance table in the MD&A of the FY25 annual report shows four business segments. Which segment reported the lowest EBIT margin and what was it?",
        "expected_answer": "The Industrial & Engineering segment reported the lowest EBIT margin at 2% on sales of ₹838 Crores in FY25, a sharp fall from 6% in FY24.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 60,
        "section": "Images",
        "difficulty": "Medium",
        "question": "The Key Financial Ratios comparison table in the FY25 MD&A shows two ratios that moved in opposite directions. Which two ratios are they and what does this divergence indicate?",
        "expected_answer": "Debt-Equity Ratio improved from 0.91x to 0.59x (QIP equity raise). Interest Coverage Ratio deteriorated from 4.24x to 3.05x (higher interest costs). The divergence reveals equity infusion strengthened the balance sheet while operating cash generation did not proportionately improve — a QIP masking effect.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 61,
        "section": "Images",
        "difficulty": "Hard",
        "question": "The BRSR Section 9 table in the FY25 report shows the number of trading houses jumped from 96 in FY24 to 532 in FY25 while the percentage of purchases from trading houses remained flat at 18%. What forensic question does this raise?",
        "expected_answer": "A 5x proliferation of trading-house vendors while the top-10 concentration drops from 50% to 37% is a classic structuring pattern. A CA must verify whether these 532 entities are independent or shells used to route transactions below individual materiality thresholds.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },
    {
        "id": 62,
        "section": "Images",
        "difficulty": "Hard",
        "question": "The commodity price risk and hedging table in the FY25 Corporate Governance Report shows NA across all fields. How does this contrast with the company's foreign exchange outgo of ₹703.30 Crores disclosed in the Directors' Report?",
        "expected_answer": "Nil commodity hedging vs ₹703.30 Cr forex outgo against only ₹196.42 Cr earnings creates a net forex deficit of ~₹507 Cr. With a new German subsidiary, leaving this unhedged is a material risk. A CA must verify whether hedging exists off-balance sheet.",
        "expected_source": ["images"],
        "expected_citation_contains": ["Annual-Report"],
    },

    # ── CROSS-SOURCE (15) ─────────────────────────────────────────────────────
    {
        "id": 63,
        "section": "Cross",
        "difficulty": "Easy",
        "question": "In the FY22 Q4 earnings call, management guided total debt reduction of ₹100 Crores for FY23. What does the Excel Balance Sheet data show as the actual change in total borrowings in FY23 — was guidance met?",
        "expected_answer": "Q4 FY22 concall guided debt reduction from ₹713 Cr to ~₹613 Cr. Excel shows FY23 borrowings at ₹1,240.23 Cr — not only was the target missed, debt nearly doubled due to the DR Axion acquisition financing.",
        "expected_source": ["excel", "concall"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "CraftsmanAutomation"],
    },
    {
        "id": 64,
        "section": "Cross",
        "difficulty": "Easy",
        "question": "The FY23 MD&A states the Interest Coverage Ratio declined from 6.40x to 5.74x due to increased interest cost. Verify this using the Excel P&L data — does the reported interest figure match?",
        "expected_answer": "Excel shows FY22 Interest = ₹84.22 Cr, FY23 Interest = ₹117 Cr — confirming the MD&A narrative. ICR from Excel: FY22 = 6.40x confirmed. Slight discrepancy in FY23 ICR suggests EBITDA definition differs between Excel and MD&A.",
        "expected_source": ["excel", "pdf"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "Annual-Report"],
    },
    {
        "id": 65,
        "section": "Cross",
        "difficulty": "Easy",
        "question": "The FY22 annual report KPI page shows a Debt/EBITDA bar chart with FY22 value of 1.33x. Verify this using the Excel data and identify any discrepancy.",
        "expected_answer": "Excel FY22: Borrowings = ₹799.55 Cr, EBITDA = ₹539 Cr. Gross D/EBITDA = 1.48x. Chart shows 1.33x — suggesting the chart uses net debt (borrowings minus cash) rather than gross borrowings.",
        "expected_source": ["excel", "images"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "Annual-Report"],
    },
    {
        "id": 66,
        "section": "Cross",
        "difficulty": "Medium",
        "question": "In the FY23 Q1 concall, management stated annualised pre-tax ROCE improved to 26% from 20% in FY22. Using Excel data, calculate ROCE for FY22 and assess whether the stated improvement is directionally accurate.",
        "expected_answer": "Excel FY22 ROCE approximately 20% — consistent with management's stated FY22 baseline. The Q1 FY23 claim of 26% is annualised from one quarter and cannot be fully verified from annual Excel data alone.",
        "expected_source": ["excel", "concall"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "CraftsmanAutomation"],
    },
    {
        "id": 67,
        "section": "Cross",
        "difficulty": "Medium",
        "question": "The FY24 Chairman's letter describes business performance as consolidation and moderation in growth. Calculate actual revenue growth and PAT growth for FY24 from Excel and assess whether moderation is accurate.",
        "expected_answer": "Excel: FY24 revenue grew 39.8% and PAT grew 27.9%. A 40% revenue growth year being described as moderation is misleading — the moderation likely refers to margin compression, not topline growth.",
        "expected_source": ["excel", "pdf"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "Annual-Report"],
    },
    {
        "id": 68,
        "section": "Cross",
        "difficulty": "Medium",
        "question": "In the FY23 Q2 concall, management claimed Aluminum segment margins were in line with Q1. The FY23 MD&A reports Aluminum segment EBIT margin for the full year. Is the full-year margin consistent with the in-call claim?",
        "expected_answer": "FY23 MD&A reports Aluminum EBIT margin at 9% for full year. FY22 Aluminum EBIT margin was also approximately 9-10%. The full-year figure is broadly consistent with management's stability claim, though Q2 specifically showed value addition compression.",
        "expected_source": ["concall", "pdf"],
        "expected_citation_contains": ["CraftsmanAutomation", "Annual-Report"],
    },
    {
        "id": 69,
        "section": "Cross",
        "difficulty": "Medium",
        "question": "The FY24 annual report donut chart shows Aluminum Products contributing 48% of consolidated revenue at ₹2,154 Cr. The MD&A shows standalone Aluminum at ₹917 Cr. Using Excel, verify the standalone Aluminum revenue figure.",
        "expected_answer": "Implied DR Axion contribution = ₹2,154 − ₹917 = ₹1,237 Cr, consistent with Board's Report disclosure of DR Axion turnover of ₹1,246 Cr. The ₹9 Cr difference is intercompany elimination.",
        "expected_source": ["excel", "pdf", "images"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "Annual-Report"],
    },
    {
        "id": 70,
        "section": "Cross",
        "difficulty": "Hard",
        "question": "Across all concall transcripts, management made multiple statements about CAPEX plans. Using Excel investing cash flows and balance sheet changes, quantify how much of the guided CAPEX was actually deployed each year.",
        "expected_answer": "Concall guided FY23 CAPEX ₹225-275 Cr. Excel investing outflows show actual capex ~₹856 Cr — significantly exceeding guidance. Management underguided by ~3x, partly explained by the DR Axion acquisition (₹375 Cr) included in investing outflows.",
        "expected_source": ["excel", "concall"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "CraftsmanAutomation"],
    },
    {
        "id": 71,
        "section": "Cross",
        "difficulty": "Hard",
        "question": "The FY25 MD&A attributes RoNW collapse of 77% to one-time expenses for acquisitions. Using Excel, calculate RoNW for FY24 and FY25 independently and assess whether the one-time explanation is sufficient.",
        "expected_answer": "FY25 PAT = ₹194.57 Cr, Networth = ₹2,856.74 Cr. RoNW FY25 = 6.8% vs FY24 ~13%. Management's one-time framing is partially misleading — the QIP equity dilution mechanically depressed RoNW regardless of one-time charges.",
        "expected_source": ["excel", "pdf"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "Annual-Report"],
    },
    {
        "id": 72,
        "section": "Cross",
        "difficulty": "Hard",
        "question": "Management guided debt reduction as a priority across multiple concall years. The FY25 MD&A shows Debt-Equity Ratio improving to 0.59x due to QIP. Using Excel borrowings data across all years, did debt actually reduce in absolute terms?",
        "expected_answer": "Excel Borrowings: FY22 ₹799 Cr → FY23 ₹1,240 Cr → FY24 ₹1,754 Cr → FY25 ₹2,358 Cr → FY26 ₹3,623 Cr. Debt rose every single year in absolute terms. The FY25 D/E improvement is entirely driven by QIP equity raise, not debt reduction. Management's narrative is factually contradicted by Excel data.",
        "expected_source": ["excel", "concall", "pdf"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "CraftsmanAutomation", "Annual-Report"],
    },
    {
        "id": 73,
        "section": "Cross",
        "difficulty": "Hard",
        "question": "The FY24 KPI page bar chart shows Debt-EBITDA rising for two consecutive years to 1.72x in FY24. Using Excel, extend this calculation to FY25 and FY26. Does the trend accelerate, stabilise, or reverse?",
        "expected_answer": "Excel FY25: Borrowings ₹2,358 Cr, EBITDA ₹833 Cr → D/EBITDA = 2.83x. The trend shown in the FY24 chart dramatically accelerates in FY25 — a fact not visible in the annual report image which only shows through FY24.",
        "expected_source": ["excel", "images"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "Annual-Report"],
    },
    {
        "id": 74,
        "section": "Cross",
        "difficulty": "Hard",
        "question": "The FY23 auditor's report identifies derivative contracts as a KAM with assets of ₹936 Lakhs and liabilities of ₹375 Lakhs. In the FY23 Q2 concall, management discussed aluminum price risk. Are these derivative positions consistent with the hedging strategy described?",
        "expected_answer": "Auditor's KAM shows net derivative asset of ₹561 Lakhs — a modest position vs ₹196 Cr quarterly aluminum revenue. The derivatives appear to be forex hedges rather than commodity hedges, meaning aluminum price risk was genuinely unhedged as management implied in the concall.",
        "expected_source": ["pdf", "concall"],
        "expected_citation_contains": ["Annual-Report", "CraftsmanAutomation"],
    },
    {
        "id": 75,
        "section": "Cross",
        "difficulty": "Hard",
        "question": "Management stated in multiple concalls that the Automotive Powertrain segment is the core earnings driver. Using Excel and the FY24 MD&A segment EBIT data, calculate what percentage of total company EBIT came from Powertrain in FY22 and FY24.",
        "expected_answer": "FY22: Powertrain EBIT ~₹333 Cr representing nearly 100% of total EBIT as other segments were near breakeven. FY24: Powertrain EBIT contribution declining as Aluminum (DR Axion) grew. The segment's EBIT dominance is clearly declining — management's concall narrative of Powertrain as core is becoming less numerically accurate.",
        "expected_source": ["excel", "pdf", "concall"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "Annual-Report", "CraftsmanAutomation"],
    },
    {
        "id": 76,
        "section": "Cross",
        "difficulty": "Hard",
        "question": "The FY25 Directors' Report discloses loans and advances to related parties jumped from 0% to 100% per BRSR data. Using Excel balance sheet data, assess whether this represents a material fund flow to subsidiaries.",
        "expected_answer": "The 0% to 100% RPT concentration shift combined with three acquisitions in FY25 (DR Axion, Sunbeam, Craftsman Germany) suggests the intercompany loans are acquisition-related funding. Absolute quantum from Excel determines materiality under IND AS 24.",
        "expected_source": ["excel", "pdf"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "Annual-Report"],
    },
    {
        "id": 77,
        "section": "Cross",
        "difficulty": "Hard",
        "question": "Across all available sources — Excel, concalls, annual report visuals, and MD&A ratios — construct a complete picture of Craftsman's debt trajectory from FY22 to FY26. Did management's stated commitment to deleveraging materialise?",
        "expected_answer": "Concall guidance: multiple commitments to ₹100 Cr debt reduction. PDF visuals: FY22 KPI chart shows D/EBITDA at 1.33x — lowest in 5 years. MD&A FY25: D/E improved to 0.59x via QIP. Excel raw data: Borrowings FY22 ₹799 Cr → FY26 ₹3,623 Cr — a 353% absolute increase. Every narrative source suggests deleveraging intent but Excel shows continuous accelerating debt accumulation. The ratio improvement in FY25 is entirely a QIP artifact.",
        "expected_source": ["excel", "concall", "pdf", "images"],
        "expected_citation_contains": ["Craftsman Auto.xlsx", "CraftsmanAutomation", "Annual-Report"],
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def fire_question(question: str, company_slug: str) -> dict:
    """Fire a question at the FinBot API and return the full response."""
    payload = {
        "question": question,
        "company_slug": company_slug,
        "year": None,
    }
    start = time.time()
    try:
        resp = requests.post(API_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        latency = round(time.time() - start, 2)
        data["latency_seconds"] = latency
        return data
    except Exception as e:
        latency = round(time.time() - start, 2)
        return {
            "answer": f"ERROR: {e}",
            "citations": [],
            "collections_searched": [],
            "agent_used": "error",
            "agent_trace": str(e),
            "chunks": [],
            "latency_seconds": latency,
        }


def check_routing(actual_sources: list, expected_sources: list) -> bool:
    """Check if routing is correct — all expected sources present in actual."""
    actual_set = set(actual_sources)
    expected_set = set(expected_sources)
    return expected_set.issubset(actual_set)


def check_citation(citations: list, expected_contains: list) -> bool:
    """Check if at least one expected string appears in citations."""
    citation_filenames = [c.get("filename", "") for c in citations]
    citation_str = " ".join(citation_filenames).lower()
    return any(term.lower() in citation_str for term in expected_contains)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"  FinBot Evaluation Run")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total questions: {len(QUESTIONS)}")
    print(f"{'='*60}\n")

    results = []
    section_stats = {}

    for i, q in enumerate(QUESTIONS, 1):
        section = q["section"]
        print(f"[{i:02d}/{len(QUESTIONS)}] {section} | {q['difficulty']} | Q{q['id']}: {q['question'][:70]}...")

        # Fire question
        response = fire_question(q["question"], COMPANY_SLUG)

        # Auto-score routing and citation
        routing_correct = check_routing(
            response.get("collections_searched", []),
            q["expected_source"]
        )
        citation_correct = check_citation(
            response.get("citations", []),
            q["expected_citation_contains"]
        )

        # Build result record
        result = {
            "id": q["id"],
            "section": section,
            "difficulty": q["difficulty"],
            "question": q["question"],
            "expected_answer": q["expected_answer"],
            "expected_source": q["expected_source"],
            "expected_citation_contains": q["expected_citation_contains"],
            "actual_answer": response.get("answer", ""),
            "actual_sources": response.get("collections_searched", []),
            "actual_citations": response.get("citations", []),
            "actual_chunks": [c.get("content", "") for c in response.get("chunks", []) if isinstance(c, dict) and "content" in c],
            "routing_debug": response.get("routing_debug", {}),
            "agent_used": response.get("agent_used", ""),
            "latency_seconds": response.get("latency_seconds", 0),
            "routing_correct": routing_correct,
            "citation_correct": citation_correct,
            "correct": None,  # To be filled manually
        }

        results.append(result)

        # Track section stats
        if section not in section_stats:
            section_stats[section] = {
                "total": 0, "routing_correct": 0,
                "citation_correct": 0, "latency_total": 0
            }
        section_stats[section]["total"] += 1
        section_stats[section]["routing_correct"] += int(routing_correct)
        section_stats[section]["citation_correct"] += int(citation_correct)
        section_stats[section]["latency_total"] += response.get("latency_seconds", 0)

        status = "✅" if routing_correct else "❌"
        print(f"         Routing: {status} | Latency: {response.get('latency_seconds', 0)}s\n")

        # Small delay to avoid rate limits
        time.sleep(1)

    # ── Save JSON ──────────────────────────────────────────────────────────────
    output = {
        "run_timestamp": TIMESTAMP,
        "total_questions": len(QUESTIONS),
        "company_slug": COMPANY_SLUG,
        "results": results,
    }

    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # ── Save TXT ───────────────────────────────────────────────────────────────
    with open(TXT_OUTPUT, "w", encoding="utf-8") as f:
        f.write(f"FinBot Evaluation Raw Results\n")
        f.write(f"Run: {TIMESTAMP}\n")
        f.write(f"{'='*80}\n\n")

        for r in results:
            f.write(f"Q{r['id']} [{r['section']}] [{r['difficulty']}]\n")
            f.write(f"Question: {r['question']}\n")
            f.write(f"Expected: {r['expected_answer']}\n")
            f.write(f"Actual:   {r['actual_answer']}\n")
            f.write(f"Routing:  {'✅' if r['routing_correct'] else '❌'} | Expected: {r['expected_source']} | Got: {r['actual_sources']}\n")
            f.write(f"Citation: {'✅' if r['citation_correct'] else '❌'}\n")
            f.write(f"Latency:  {r['latency_seconds']}s\n")
            f.write(f"Correct:  [FILL MANUALLY: true/false]\n")
            f.write(f"{'-'*80}\n\n")

        # ── Auto-scored summary ────────────────────────────────────────────────
        f.write(f"\n{'='*80}\n")
        f.write(f"AUTO-SCORED SUMMARY (Routing + Citation + Latency)\n")
        f.write(f"{'='*80}\n\n")

        total_routing = sum(1 for r in results if r["routing_correct"])
        total_citation = sum(1 for r in results if r["citation_correct"])
        avg_latency = sum(r["latency_seconds"] for r in results) / len(results)

        f.write(f"Overall Routing Accuracy:  {total_routing}/{len(results)} = {total_routing/len(results)*100:.1f}%\n")
        f.write(f"Overall Citation Accuracy: {total_citation}/{len(results)} = {total_citation/len(results)*100:.1f}%\n")
        f.write(f"Average Latency:           {avg_latency:.2f}s\n\n")

        f.write(f"Per Section:\n")
        for section, stats in section_stats.items():
            n = stats["total"]
            r_pct = stats["routing_correct"] / n * 100
            c_pct = stats["citation_correct"] / n * 100
            avg_lat = stats["latency_total"] / n
            f.write(f"  {section:<10} Routing: {stats['routing_correct']}/{n} ({r_pct:.0f}%) | Citation: {stats['citation_correct']}/{n} ({c_pct:.0f}%) | Avg Latency: {avg_lat:.1f}s\n")

    # ── Print summary ──────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  EVALUATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Total questions:   {len(results)}")
    print(f"  Routing accuracy:  {total_routing}/{len(results)} ({total_routing/len(results)*100:.1f}%)")
    print(f"  Citation accuracy: {total_citation}/{len(results)} ({total_citation/len(results)*100:.1f}%)")
    print(f"  Avg latency:       {avg_latency:.2f}s")
    print(f"\n  Results saved to:")
    print(f"  JSON: {JSON_OUTPUT}")
    print(f"  TXT:  {TXT_OUTPUT}")
    print(f"\n  Next steps:")
    print(f"  1. Open {TXT_OUTPUT} and mark correct: true/false for each answer")
    print(f"  2. Update the JSON file with your manual correct values")
    print(f"  3. Run score_eval.py to get full metrics including RAGAS")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()