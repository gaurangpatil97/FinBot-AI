"""
Financial Intelligence RAG System — 150Q Master Benchmark
Tests all 5 experiments across all modalities
Run: python test_150q_master.py
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1/query"
TIMEOUT = 120
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "results"

QA_PAIRS = [

    # ══════════════════════════════════════════════════════
    # SECTION 1: EXCEL — Direct Financial Figures (Q1-Q30)
    # ══════════════════════════════════════════════════════

    # L1 Direct Lookup
    {
        "id": 1, "section": "Excel", "level": "L1-Direct",
        "question": "What was Craftsman Automation's total sales revenue in FY2022?",
        "expected_answer": "2217.02 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 2, "section": "Excel", "level": "L1-Direct",
        "question": "What was the net profit (PAT) of Craftsman Automation in FY2022?",
        "expected_answer": "163.09 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 3, "section": "Excel", "level": "L1-Direct",
        "question": "What were the total borrowings of Craftsman Automation in FY2022?",
        "expected_answer": "799.55 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 4, "section": "Excel", "level": "L1-Direct",
        "question": "What was the depreciation amount for Craftsman Automation in FY2022?",
        "expected_answer": "205.99 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 5, "section": "Excel", "level": "L1-Direct",
        "question": "What was the EBITDA of Craftsman Automation in FY2022?",
        "expected_answer": "502.72 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 6, "section": "Excel", "level": "L1-Direct",
        "question": "What was the interest expense of Craftsman Automation in FY2022?",
        "expected_answer": "84.22 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 7, "section": "Excel", "level": "L1-Direct",
        "question": "What was the networth of Craftsman Automation in FY2022?",
        "expected_answer": "1135.74 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 8, "section": "Excel", "level": "L1-Direct",
        "question": "What was the PBT of Craftsman Automation in FY2022?",
        "expected_answer": "251.73 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 9, "section": "Excel", "level": "L1-Direct",
        "question": "What was the cash from operations for Craftsman Automation in FY2022?",
        "expected_answer": "327.21 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 10, "section": "Excel", "level": "L1-Direct",
        "question": "What was the net cash flow for Craftsman Automation in FY2022?",
        "expected_answer": "-1.84 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },

    # L2 Derived Calculations
    {
        "id": 11, "section": "Excel", "level": "L2-Derived",
        "question": "What was the EBITDA margin percentage for Craftsman Automation in FY2022?",
        "expected_answer": "~22.7%",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 12, "section": "Excel", "level": "L2-Derived",
        "question": "What was the net profit margin for Craftsman Automation in FY2022?",
        "expected_answer": "~7.4%",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 13, "section": "Excel", "level": "L2-Derived",
        "question": "What was the debt to equity ratio for Craftsman Automation in FY2022?",
        "expected_answer": "~0.70",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 14, "section": "Excel", "level": "L2-Derived",
        "question": "What was the debt to EBITDA ratio for Craftsman Automation in FY2022?",
        "expected_answer": "~1.59",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 15, "section": "Excel", "level": "L2-Derived",
        "question": "Calculate the interest coverage ratio for Craftsman Automation in FY2022.",
        "expected_answer": "~2.99",
        "expected_source": "Craftsman Auto.xlsx"
    },

    # L3 Cross-year
    {
        "id": 16, "section": "Excel", "level": "L3-CrossYear",
        "question": "How did Craftsman Automation's revenue grow from FY2021 to FY2022?",
        "expected_answer": "FY21: ~1546 Cr, FY22: 2217 Cr, growth ~43%",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 17, "section": "Excel", "level": "L3-CrossYear",
        "question": "Compare the net profit of Craftsman Automation between FY2021 and FY2022.",
        "expected_answer": "FY21: ~97 Cr, FY22: 163 Cr",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 18, "section": "Excel", "level": "L3-CrossYear",
        "question": "What was the revenue CAGR of Craftsman Automation from FY2019 to FY2022?",
        "expected_answer": "~15-20% CAGR",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 19, "section": "Excel", "level": "L3-CrossYear",
        "question": "How did borrowings change from FY2020 to FY2022 for Craftsman Automation?",
        "expected_answer": "Trend from FY20 to FY22",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 20, "section": "Excel", "level": "L3-CrossYear",
        "question": "What was the highest ever EBITDA recorded by Craftsman Automation across all years?",
        "expected_answer": "From available data",
        "expected_source": "Craftsman Auto.xlsx"
    },

    {
        "id": 21, "section": "Excel", "level": "L1-Direct",
        "question": "What was Craftsman Automation's total sales revenue in FY2025?",
        "expected_answer": "From Excel data",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 22, "section": "Excel", "level": "L1-Direct",
        "question": "What was Craftsman Automation's net profit (PAT) in FY2025?",
        "expected_answer": "From Excel data",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 23, "section": "Excel", "level": "L1-Direct",
        "question": "What was Craftsman Automation's EBITDA in FY2025?",
        "expected_answer": "From Excel data",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 24, "section": "Excel", "level": "L1-Direct",
        "question": "What were Craftsman Automation's total borrowings in FY2025?",
        "expected_answer": "From Excel data",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 25, "section": "Excel", "level": "L1-Direct",
        "question": "What was Craftsman Automation's networth in FY2025?",
        "expected_answer": "From Excel data",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 26, "section": "Excel", "level": "L2-Derived",
        "question": "What was Craftsman Automation's EBITDA margin in FY2025?",
        "expected_answer": "From Excel data",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 27, "section": "Excel", "level": "L2-Derived",
        "question": "What was Craftsman Automation's net profit margin in FY2025?",
        "expected_answer": "From Excel data",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 28, "section": "Excel", "level": "L3-CrossYear",
        "question": "How did Craftsman Automation's revenue grow from FY2024 to FY2025?",
        "expected_answer": "From Excel data",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 29, "section": "Excel", "level": "L3-CrossYear",
        "question": "Compare Craftsman Automation's net profit margin in FY2022 vs FY2025.",
        "expected_answer": "From Excel data",
        "expected_source": "Craftsman Auto.xlsx"
    },
    {
        "id": 30, "section": "Excel", "level": "L1-Direct",
        "question": "What was Craftsman Automation's cash from operations in FY2025?",
        "expected_answer": "From Excel data",
        "expected_source": "Craftsman Auto.xlsx"
    },

    # ══════════════════════════════════════════════════════
    # SECTION 2: IMAGE — Visual/Chart Data (Q31-Q60)
    # ══════════════════════════════════════════════════════

    {
        "id": 31, "section": "Image", "level": "L1-Direct",
        "question": "What was Craftsman Automation's revenue as shown in the FY22 annual report charts?",
        "expected_answer": "~2206 Cr",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 32, "section": "Image", "level": "L1-Direct",
        "question": "What was the EBITDA shown in the Craftsman FY22 annual report image pages?",
        "expected_answer": "539 Cr",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 33, "section": "Image", "level": "L1-Direct",
        "question": "What was Craftsman Automation's net profit as shown in FY22 annual report visuals?",
        "expected_answer": "~160 Cr",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 34, "section": "Image", "level": "L1-Direct",
        "question": "What was the market cap of Craftsman Automation shown in FY22 annual report?",
        "expected_answer": "4983 Cr",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 35, "section": "Image", "level": "L1-Direct",
        "question": "What percentage of Craftsman Automation revenue was domestic vs exports in FY22?",
        "expected_answer": "Domestic 92%, Exports 8%",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 36, "section": "Image", "level": "L1-Direct",
        "question": "What was the powertrain segment revenue share in Craftsman FY22 annual report?",
        "expected_answer": "52%",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 37, "section": "Image", "level": "L1-Direct",
        "question": "What was the aluminum segment revenue share in Craftsman FY22 annual report?",
        "expected_answer": "20%",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 38, "section": "Image", "level": "L1-Direct",
        "question": "What was the industrial segment revenue share in Craftsman FY22 annual report?",
        "expected_answer": "28%",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 39, "section": "Image", "level": "L1-Direct",
        "question": "What was Craftsman Automation's ROCE shown in the FY22 annual report visuals?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 40, "section": "Image", "level": "L1-Direct",
        "question": "How many operating units does Craftsman Automation have as shown in FY22 report?",
        "expected_answer": "10",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 41, "section": "Image", "level": "L1-Direct",
        "question": "What was the revenue from operations shown in Craftsman FY22 image pages?",
        "expected_answer": "~2206 Cr",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 42, "section": "Image", "level": "L1-Direct",
        "question": "What percentage of Craftsman powertrain revenue comes from commercial vehicles?",
        "expected_answer": "~54%",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 43, "section": "Image", "level": "L1-Direct",
        "question": "What was Craftsman Automation's employee count shown in FY22 annual report?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 44, "section": "Image", "level": "L1-Direct",
        "question": "What was the return on equity shown in Craftsman FY22 annual report visuals?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 45, "section": "Image", "level": "L1-Direct",
        "question": "How many manufacturing plants does Craftsman Automation operate as per FY22 report?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 46, "section": "Image", "level": "L1-Direct",
        "question": "What was Craftsman Automation's debt to equity ratio shown in FY22 annual report charts?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 47, "section": "Image", "level": "L1-Direct",
        "question": "What was the EPS shown in Craftsman FY22 annual report?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 48, "section": "Image", "level": "L1-Direct",
        "question": "What is Craftsman Automation's revenue split between auto and non-auto segments?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 49, "section": "Image", "level": "L1-Direct",
        "question": "What was the storage solutions revenue growth shown in Craftsman FY22 report?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 50, "section": "Image", "level": "L1-Direct",
        "question": "What percentage of Craftsman revenue comes from farm sector as shown in FY22 charts?",
        "expected_answer": "~18%",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 51, "section": "Image", "level": "L1-Direct",
        "question": "What was the off-highway segment contribution to powertrain revenue in FY22?",
        "expected_answer": "~20%",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 52, "section": "Image", "level": "L1-Direct",
        "question": "What was Craftsman Automation's total capex shown in FY22 annual report?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 53, "section": "Image", "level": "L1-Direct",
        "question": "What is the geographic revenue split shown in Craftsman FY22 annual report?",
        "expected_answer": "Domestic 92%, Export 8%",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 54, "section": "Image", "level": "L1-Direct",
        "question": "What was Craftsman Automation's book value per share shown in FY22 report?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 55, "section": "Image", "level": "L1-Direct",
        "question": "What was the current ratio of Craftsman Automation shown in FY22 annual report?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 56, "section": "Image", "level": "L1-Direct",
        "question": "What was Craftsman Automation's revenue per employee shown in FY22 report?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 57, "section": "Image", "level": "L1-Direct",
        "question": "What was the working capital days shown in Craftsman FY22 annual report?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 58, "section": "Image", "level": "L1-Direct",
        "question": "What was Craftsman Automation's asset turnover ratio shown in FY22 charts?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 59, "section": "Image", "level": "L1-Direct",
        "question": "What percentage of Craftsman revenue came from passenger vehicles in FY22?",
        "expected_answer": "~8%",
        "expected_source": "craftsman_fy22_images"
    },
    {
        "id": 60, "section": "Image", "level": "L1-Direct",
        "question": "What was the inventory turnover shown in Craftsman FY22 annual report visuals?",
        "expected_answer": "From image data",
        "expected_source": "craftsman_fy22_images"
    },

    # ══════════════════════════════════════════════════════
    # SECTION 3: PDF TEXT — Narrative/Strategy (Q61-Q90)
    # ══════════════════════════════════════════════════════

    {
        "id": 61, "section": "PDF Text", "level": "L1-Direct",
        "question": "What are the key business segments of Craftsman Automation as described in the annual report?",
        "expected_answer": "Powertrain, Aluminum Products, Industrial Engineering",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 62, "section": "PDF Text", "level": "L1-Direct",
        "question": "What are the main risk factors mentioned in Craftsman Automation FY22 annual report?",
        "expected_answer": "Commodity prices, competition, regulatory risks",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 63, "section": "PDF Text", "level": "L1-Direct",
        "question": "What is Craftsman Automation's stated growth strategy in the FY22 annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 64, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does the MD&A section say about Craftsman's powertrain business outlook?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 65, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does Craftsman Automation annual report say about EV transition risks?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 66, "section": "PDF Text", "level": "L1-Direct",
        "question": "What is the storage solutions business strategy described in Craftsman FY22 annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 67, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does the directors report say about Craftsman Automation's performance in FY22?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 68, "section": "PDF Text", "level": "L1-Direct",
        "question": "What are Craftsman Automation's key competitive advantages mentioned in the annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 69, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does Craftsman annual report say about their aluminum business capacity expansion?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 70, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does the Craftsman FY22 annual report say about the MHCV industry outlook?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 71, "section": "PDF Text", "level": "L1-Direct",
        "question": "What are the key raw material risks mentioned in Craftsman annual report?",
        "expected_answer": "Steel, aluminum price volatility",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 72, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does Craftsman annual report say about their export strategy?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 73, "section": "PDF Text", "level": "L1-Direct",
        "question": "What is mentioned about Craftsman Automation's quality certifications in the annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 74, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does the Craftsman annual report say about their R&D activities?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 75, "section": "PDF Text", "level": "L1-Direct",
        "question": "What corporate governance practices are highlighted in Craftsman FY22 annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 76, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does the Craftsman annual report say about their ESG initiatives?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 77, "section": "PDF Text", "level": "L1-Direct",
        "question": "What are the key customers mentioned in Craftsman Automation annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 78, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does the Craftsman annual report say about their debt reduction plan?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 79, "section": "PDF Text", "level": "L1-Direct",
        "question": "What technology investments does Craftsman mention in their FY22 annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 80, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does the Craftsman annual report say about their human resources and workforce?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 81, "section": "PDF Text", "level": "L1-Direct",
        "question": "What is mentioned about Craftsman Automation's Nagpur plant expansion in annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 82, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does the auditor report say about Craftsman Automation's financial statements?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 83, "section": "PDF Text", "level": "L1-Direct",
        "question": "What industry trends are highlighted in Craftsman FY22 annual report MD&A?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 84, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does Craftsman annual report say about commodity price passthrough mechanism?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 85, "section": "PDF Text", "level": "L1-Direct",
        "question": "What are the related party transactions mentioned in Craftsman FY22 annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 86, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does Craftsman annual report say about their dividend policy?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 87, "section": "PDF Text", "level": "L1-Direct",
        "question": "What is mentioned about Craftsman Automation's liquidity position in annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 88, "section": "PDF Text", "level": "L1-Direct",
        "question": "What capital allocation strategy does Craftsman management describe in annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 89, "section": "PDF Text", "level": "L1-Direct",
        "question": "What does Craftsman annual report say about their two-wheeler customer concentration risk?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },
    {
        "id": 90, "section": "PDF Text", "level": "L1-Direct",
        "question": "What is the Craftsman Automation business description and history in annual report?",
        "expected_answer": "From PDF narrative",
        "expected_source": "Annual Report PDF"
    },

    # ══════════════════════════════════════════════════════
    # SECTION 4: CONCALL — Management Commentary (Q91-Q120)
    # ══════════════════════════════════════════════════════

    {
        "id": 91, "section": "Concall", "level": "L1-Direct",
        "question": "What was the total turnover for nine months ended December 2021 mentioned in the Q3 FY22 concall?",
        "expected_answer": "1552 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Feb.pdf"
    },
    {
        "id": 92, "section": "Concall", "level": "L1-Direct",
        "question": "What CAPEX guidance did management give for FY23 in the Q3 FY22 concall?",
        "expected_answer": "~200 Cr maintenance + growth",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Feb.pdf"
    },
    {
        "id": 93, "section": "Concall", "level": "L1-Direct",
        "question": "What was the capacity utilization of auto powertrain in Q3 FY22 per management?",
        "expected_answer": "Less than 60%",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Feb.pdf"
    },
    {
        "id": 94, "section": "Concall", "level": "L1-Direct",
        "question": "What was the highest ever annual sales reported in the Q4 FY22 earnings call?",
        "expected_answer": "2200 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_May.pdf"
    },
    {
        "id": 95, "section": "Concall", "level": "L1-Direct",
        "question": "What EBITDA did management report in the Q4 FY22 concall?",
        "expected_answer": "539 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_May.pdf"
    },
    {
        "id": 96, "section": "Concall", "level": "L1-Direct",
        "question": "What growth rate did management guide for storage solutions in FY23?",
        "expected_answer": "Minimum 50%",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_May.pdf"
    },
    {
        "id": 97, "section": "Concall", "level": "L1-Direct",
        "question": "What did management say about the Daimler engine transition risk to Cummins?",
        "expected_answer": "8-9% impact by FY27-28",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_May.pdf"
    },
    {
        "id": 98, "section": "Concall", "level": "L1-Direct",
        "question": "What credit rating upgrade was announced in the Q1 FY23 earnings call?",
        "expected_answer": "A+ with stable outlook",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_July.pdf"
    },
    {
        "id": 99, "section": "Concall", "level": "L1-Direct",
        "question": "What segment restructuring did management announce in Q1 FY23?",
        "expected_answer": "Industrial aluminum merged with auto aluminum into Aluminum Products segment",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_July.pdf"
    },
    {
        "id": 100, "section": "Concall", "level": "L1-Direct",
        "question": "What growth CAGR did management guide for the next 3-4 years in the July 2022 concall?",
        "expected_answer": "20%",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_July.pdf"
    },
    {
        "id": 101, "section": "Concall", "level": "L1-Direct",
        "question": "What was the overall capacity utilization across businesses in Q1 FY23?",
        "expected_answer": "Closing to 70%",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_July.pdf"
    },
    {
        "id": 102, "section": "Concall", "level": "L1-Direct",
        "question": "What was the H1 FY23 sales figure and how much higher was it vs H1 last year?",
        "expected_answer": "1447 Cr vs 1000 Cr, 45% higher",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct1.pdf"
    },
    {
        "id": 103, "section": "Concall", "level": "L1-Direct",
        "question": "What was the revised CAPEX guidance for full year FY23 in the October 2022 concall?",
        "expected_answer": "275 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct1.pdf"
    },
    {
        "id": 104, "section": "Concall", "level": "L1-Direct",
        "question": "What was the value addition for auto powertrain in Q2 FY23?",
        "expected_answer": "232 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct1.pdf"
    },
    {
        "id": 105, "section": "Concall", "level": "L1-Direct",
        "question": "What was the H1 FY23 storage solutions revenue?",
        "expected_answer": "199 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct1.pdf"
    },
    {
        "id": 106, "section": "Concall", "level": "L1-Direct",
        "question": "What was the aluminum segment revenue mix two-wheeler vs passenger vehicle in Q2 FY23?",
        "expected_answer": "Two-wheeler 68%, PV 2%, CV 9%",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct1.pdf"
    },
    {
        "id": 107, "section": "Concall", "level": "L1-Direct",
        "question": "What was the total borrowings level mentioned in October 2022 concall?",
        "expected_answer": "720 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct2.pdf"
    },
    {
        "id": 108, "section": "Concall", "level": "L1-Direct",
        "question": "What did management say about the Stellantis PSA order production start timeline?",
        "expected_answer": "Q2 or Q3 of next financial year FY24",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct2.pdf"
    },
    {
        "id": 109, "section": "Concall", "level": "L1-Direct",
        "question": "What was the powertrain EBIT for H1 FY23 mentioned in the concall?",
        "expected_answer": "188 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct2.pdf"
    },
    {
        "id": 110, "section": "Concall", "level": "L1-Direct",
        "question": "What was the storage solutions revenue for full year FY22 mentioned in concall?",
        "expected_answer": "253 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_May.pdf"
    },
    {
        "id": 111, "section": "Concall", "level": "L1-Direct",
        "question": "What was the debt level as of March 2022 mentioned in Q4 FY22 concall?",
        "expected_answer": "713 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_May.pdf"
    },
    {
        "id": 112, "section": "Concall", "level": "L1-Direct",
        "question": "What revenue capacity per month did management claim at full utilization?",
        "expected_answer": "300 Cr per month",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_May.pdf"
    },
    {
        "id": 113, "section": "Concall", "level": "L1-Direct",
        "question": "What did management say about Daimler Brazil business timeline in July 2022 concall?",
        "expected_answer": "Protected until 2028",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_July.pdf"
    },
    {
        "id": 114, "section": "Concall", "level": "L1-Direct",
        "question": "What was the powertrain revenue mix by segment for H1 FY23?",
        "expected_answer": "CV 385 Cr, Off-highway 150 Cr, Farm 125 Cr, PV 66 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct1.pdf"
    },
    {
        "id": 115, "section": "Concall", "level": "L1-Direct",
        "question": "What did management say about EV two-wheeler opportunity in October 2022 concall?",
        "expected_answer": "Numbers not appealing, EV sales factored in next year only",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct1.pdf"
    },
    {
        "id": 116, "section": "Concall", "level": "L1-Direct",
        "question": "What was the CAPEX guidance for FY23 reaffirmed in the July 2022 concall?",
        "expected_answer": "225 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_July.pdf"
    },
    {
        "id": 117, "section": "Concall", "level": "L1-Direct",
        "question": "What was the PAT for nine months ended December 2021 and why was it significant?",
        "expected_answer": "109 Cr, highest ever, crossed previous full year PAT of 97 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Feb.pdf"
    },
    {
        "id": 118, "section": "Concall", "level": "L1-Direct",
        "question": "What was the aluminum products EBIT for H1 FY23?",
        "expected_answer": "35 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct1.pdf"
    },
    {
        "id": 119, "section": "Concall", "level": "L1-Direct",
        "question": "What was the industrial engineering EBIT for H1 FY23 vs H1 last year?",
        "expected_answer": "35 Cr vs 6 Cr",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct1.pdf"
    },
    {
        "id": 120, "section": "Concall", "level": "L1-Direct",
        "question": "What new aluminum order received in April 2022 required additional CAPEX of 70 crores?",
        "expected_answer": "New customer order, additional 70 Cr CAPEX",
        "expected_source": "CraftsmanAutomationAudioTranscript2022_Oct1.pdf"
    },

    # ══════════════════════════════════════════════════════
    # SECTION 5: CROSS-SOURCE — Multi-Modality (Q121-Q150)
    # ══════════════════════════════════════════════════════

    # Concall guidance vs Excel actuals
    {
        "id": 121, "section": "Cross", "level": "Concall+Excel",
        "question": "Management guided 50% storage solutions growth in FY23 — what does the Excel data show for actual FY23 storage revenue vs FY22?",
        "expected_answer": "FY22: 253 Cr (concall), check FY23 actual in Excel",
        "expected_source": "Both"
    },
    {
        "id": 122, "section": "Cross", "level": "Concall+Excel",
        "question": "Management guided 20% revenue CAGR — what was the actual revenue growth from FY22 to FY23 per Excel?",
        "expected_answer": "Compare guidance vs actual",
        "expected_source": "Both"
    },
    {
        "id": 123, "section": "Cross", "level": "Concall+Excel",
        "question": "Management said debt was 713 Cr as of March 2022 — does the Excel balance sheet confirm this?",
        "expected_answer": "Cross verify concall vs Excel",
        "expected_source": "Both"
    },
    {
        "id": 124, "section": "Cross", "level": "Concall+Excel",
        "question": "Management claimed EBITDA of 539 Cr for FY22 in May concall — what does Excel show?",
        "expected_answer": "Concall: 539 Cr, Excel: 502.72 Cr — different methodology",
        "expected_source": "Both"
    },
    {
        "id": 125, "section": "Cross", "level": "Concall+Excel",
        "question": "Management guided debt reduction of 100 Cr from FY22 levels — what do borrowings show in FY23 Excel?",
        "expected_answer": "Cross verify",
        "expected_source": "Both"
    },
    {
        "id": 126, "section": "Cross", "level": "Image+Excel",
        "question": "The FY22 annual report shows EBITDA of 539 Cr but Excel shows 502 Cr — explain the difference.",
        "expected_answer": "Different EBITDA methodologies — image uses different calculation",
        "expected_source": "Both"
    },
    {
        "id": 127, "section": "Cross", "level": "Image+Excel",
        "question": "Annual report shows domestic revenue at 92% — calculate absolute domestic revenue using Excel total sales.",
        "expected_answer": "92% of 2217 Cr = ~2040 Cr",
        "expected_source": "Both"
    },
    {
        "id": 128, "section": "Cross", "level": "Image+Excel",
        "question": "The annual report shows powertrain at 52% revenue share — what is the absolute powertrain revenue per Excel?",
        "expected_answer": "52% of total revenue from Excel",
        "expected_source": "Both"
    },
    {
        "id": 129, "section": "Cross", "level": "Image+Excel",
        "question": "Annual report shows market cap of 4983 Cr — is this consistent with the financial performance shown in Excel?",
        "expected_answer": "Cross verify valuation vs financials",
        "expected_source": "Both"
    },
    {
        "id": 130, "section": "Cross", "level": "Image+Excel",
        "question": "FY22 report shows 10 operating units — what is the revenue per operating unit based on Excel sales data?",
        "expected_answer": "2217/10 = ~221 Cr per unit",
        "expected_source": "Both"
    },
    {
        "id": 131, "section": "Cross", "level": "Concall+PDF",
        "question": "Management mentioned EV opportunity in concall — what does the annual report strategy section say about EV?",
        "expected_answer": "Cross reference management commentary vs formal strategy",
        "expected_source": "Both"
    },
    {
        "id": 132, "section": "Cross", "level": "Concall+PDF",
        "question": "Management said storage solutions will grow 50% — what does the annual report say about storage solutions market opportunity?",
        "expected_answer": "Cross reference guidance vs strategy",
        "expected_source": "Both"
    },
    {
        "id": 133, "section": "Cross", "level": "Concall+PDF",
        "question": "Management mentioned MHCV industry recovery in concall — does the annual report MD&A corroborate this?",
        "expected_answer": "Cross reference",
        "expected_source": "Both"
    },
    {
        "id": 134, "section": "Cross", "level": "Concall+PDF",
        "question": "Management discussed debt reduction in concall — what does the annual report say about capital structure strategy?",
        "expected_answer": "Cross reference",
        "expected_source": "Both"
    },
    {
        "id": 135, "section": "Cross", "level": "Concall+PDF",
        "question": "Management said Daimler transition risk is manageable — what does annual report risk section say about customer concentration?",
        "expected_answer": "Cross reference management commentary vs formal risk disclosure",
        "expected_source": "Both"
    },
    {
        "id": 136, "section": "Cross", "level": "Excel+PDF",
        "question": "What does the annual report narrative say about why EBITDA margins dropped, and does the Excel data confirm?",
        "expected_answer": "Commodity prices, Excel shows margin compression",
        "expected_source": "Both"
    },
    {
        "id": 137, "section": "Cross", "level": "Excel+PDF",
        "question": "Annual report mentions 43% revenue growth in FY22 — verify this with Excel data.",
        "expected_answer": "FY21 to FY22 growth calculation from Excel",
        "expected_source": "Both"
    },
    {
        "id": 138, "section": "Cross", "level": "Excel+PDF",
        "question": "Annual report mentions highest ever PAT — does Excel data confirm FY22 was the peak PAT year?",
        "expected_answer": "Cross verify across years",
        "expected_source": "Both"
    },
    {
        "id": 139, "section": "Cross", "level": "Excel+PDF",
        "question": "What CAPEX does the annual report mention, and does it match the Excel cash flow statement?",
        "expected_answer": "Cross verify CAPEX figures",
        "expected_source": "Both"
    },
    {
        "id": 140, "section": "Cross", "level": "Excel+PDF",
        "question": "Annual report states debt to equity improved — verify with Excel balance sheet data for FY21 vs FY22.",
        "expected_answer": "Cross verify ratio improvement",
        "expected_source": "Both"
    },
    {
        "id": 141, "section": "Cross", "level": "Concall+Excel+Image",
        "question": "Three sources mention different EBITDA for FY22 — reconcile the numbers from Excel, image, and concall.",
        "expected_answer": "Excel: 502 Cr, Image: 539 Cr, Concall: 539 Cr — methodology difference",
        "expected_source": "All three"
    },
    {
        "id": 142, "section": "Cross", "level": "Concall+Excel+Image",
        "question": "What is the complete financial picture of Craftsman Automation for FY22 combining all sources?",
        "expected_answer": "Comprehensive summary from all modalities",
        "expected_source": "All three"
    },
    {
        "id": 143, "section": "Cross", "level": "Concall+Excel",
        "question": "Management guided 20% growth for FY23 in July concall — what was actual FY23 revenue growth per Excel?",
        "expected_answer": "Cross verify guidance vs actuals",
        "expected_source": "Both"
    },
    {
        "id": 144, "section": "Cross", "level": "Concall+Excel",
        "question": "Management said ROCE was 20% in FY22 — does Excel data confirm this?",
        "expected_answer": "Cross verify ROCE",
        "expected_source": "Both"
    },
    {
        "id": 145, "section": "Cross", "level": "Concall+Excel",
        "question": "Management claimed ROE of 15% for FY22 — verify with Excel networth and PAT data.",
        "expected_answer": "163/1135 = ~14.4%, roughly confirms",
        "expected_source": "Both"
    },
    {
        "id": 146, "section": "Cross", "level": "Image+Concall",
        "question": "Annual report shows powertrain at 52% revenue — management said CV is 54% of powertrain. What is CV as % of total?",
        "expected_answer": "52% x 54% = ~28% of total",
        "expected_source": "Both"
    },
    {
        "id": 147, "section": "Cross", "level": "Concall+Excel",
        "question": "Management said they expect 100 Cr debt reduction in FY23 — what was actual borrowings change in Excel?",
        "expected_answer": "Cross verify",
        "expected_source": "Both"
    },
    {
        "id": 148, "section": "Cross", "level": "Concall+Excel",
        "question": "Management guided aluminum revenue to reach 1000 Cr by FY26 — what is the current trajectory from Excel?",
        "expected_answer": "Cross verify target vs trend",
        "expected_source": "Both"
    },
    {
        "id": 149, "section": "Cross", "level": "PDF+Concall",
        "question": "Annual report discusses Stellantis order as growth driver — what timeline did management give in concall?",
        "expected_answer": "Production start Q2-Q3 FY24",
        "expected_source": "Both"
    },
    {
        "id": 150, "section": "Cross", "level": "All",
        "question": "Give a complete investment thesis for Craftsman Automation based on all available data — financials, management commentary, strategy, and visual KPIs.",
        "expected_answer": "Comprehensive multi-source analysis",
        "expected_source": "All sources"
    },
]


def check_match(expected, cited_files):
    # ── Cross-source questions: require citations from BOTH relevant source types ──
    if expected in ["Both", "All sources", "All three"]:
        cited_lower = [f.lower() for f in cited_files]

        has_excel = any(
            "craftsman auto" in f or "craftsman_auto" in f or "infosys" in f
            for f in cited_lower
        )
        has_concall = any(
            "transcript" in f or "concall" in f
            for f in cited_lower
        )
        has_image = any(
            "craftsman_fy22" in f or "annual_report_image" in f or "fy22_image" in f
            for f in cited_lower
        )
        has_pdf = any(
            "annual-report" in f or "annual_report" in f
            for f in cited_lower
        )

        if expected == "Both":
            # Accept any two-source combination that makes sense for the question
            return (has_excel and has_concall) or \
                   (has_excel and has_image) or \
                   (has_excel and has_pdf) or \
                   (has_concall and has_pdf) or \
                   (has_concall and has_image) or \
                   (has_image and has_pdf)
        elif expected == "All three":
            return (has_excel or has_image) and has_concall and has_pdf
        elif expected == "All sources":
            return has_excel and has_concall and (has_image or has_pdf)

    # ── Single-source questions: keyword matching ──
    keywords = {
        # PDF Text — match any annual report PDF filename
        "Annual Report PDF": [
            "annual-report", "annual_report",
            "craftsman-automation-annual", "craftsman_annual",
            "craftsman_automation_ltd_pdf"
        ],
        # Image — must match the image collection specifically, NOT pdf filenames
        "craftsman_fy22_images": [
            "craftsman_fy22_images", "fy22_images",
            "craftsman_fy22_annual_report_images", "craftsman_automation_ltd_images"
        ],
        # Excel
        "Craftsman Auto.xlsx": ["craftsman auto", "craftsman_auto", "craftsman auto.xlsx", "craftsman_automation_ltd_excel"],
        "Infosys.xlsx": ["infosys"],
        # Concall transcripts — exact filename fragments
        "Concall transcripts": ["craftsman_automation_ltd_concalls", "concall transcripts"],
        "CraftsmanAutomationAudioTranscript2022_Feb.pdf": [
            "transcript2022_feb", "audiotranscript2022_feb",
            "2022_feb", "feb.pdf"
        ],
        "CraftsmanAutomationAudioTranscript2022_May.pdf": [
            "transcript2022_may", "audiotranscript2022_may",
            "2022_may", "may.pdf"
        ],
        "CraftsmanAutomationAudioTranscript2022_July.pdf": [
            "transcript2022_july", "audiotranscript2022_july",
            "2022_july", "july.pdf"
        ],
        "CraftsmanAutomationAudioTranscript2022_Oct1.pdf": [
            "transcript2022_oct1", "audiotranscript2022_oct1",
            "2022_oct1", "oct1.pdf"
        ],
        "CraftsmanAutomationAudioTranscript2022_Oct2.pdf": [
            "transcript2022_oct2", "audiotranscript2022_oct2",
            "2022_oct2", "oct2.pdf"
        ],
    }

    search_terms = keywords.get(expected, [expected.lower()])
    # Also try the raw expected string itself as a fallback
    if expected.lower() not in [t.lower() for t in search_terms]:
        search_terms.append(expected.lower())

    for f in cited_files:
        for term in search_terms:
            if term.lower() in f.lower():
                return True
    return False


def run_test():
    print("\n" + "="*80)
    print("FINANCIAL INTELLIGENCE RAG — 150Q MASTER BENCHMARK")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    results = []
    section_scores = {
        "Excel": {"correct": 0, "total": 0},
        "Image": {"correct": 0, "total": 0},
        "PDF Text": {"correct": 0, "total": 0},
        "Concall": {"correct": 0, "total": 0},
        "Cross": {"correct": 0, "total": 0},
    }

    for qa in QA_PAIRS:
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
                        cited_files.append(c.get("collection", ""))  # ADD THIS LINE
                    elif isinstance(c, str):
                        cited_files.append(c)

                # Check if expected source appears in citations
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

    # Final summary
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)

    total_correct = sum(s["correct"] for s in section_scores.values())
    total_questions = sum(s["total"] for s in section_scores.values())

    print(f"\n{'Section':<15} {'Score':<10} {'Percentage'}")
    print("─"*40)
    for section, scores in section_scores.items():
        if scores["total"] > 0:
            pct = scores["correct"] / scores["total"] * 100
            print(f"{section:<15} {scores['correct']}/{scores['total']:<8} {pct:.1f}%")

    print("─"*40)
    overall_pct = total_correct / total_questions * 100 if total_questions > 0 else 0
    print(f"{'TOTAL':<15} {total_correct}/{total_questions:<8} {overall_pct:.1f}%")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Save results to JSON for analysis
    json_path = OUTPUT_DIR / "150QmasterCraftsmanAutomation.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_score": f"{total_correct}/{total_questions}",
            "section_scores": section_scores,
            "results": results
        }, f, indent=2)

    # Save full text results
    results_txt_path = OUTPUT_DIR / "150QmasterCraftsmanAutomation.txt"
    with open(results_txt_path, "w", encoding="utf-8") as f:
        for item in results:
            q_id = item.get("id", 0)
            section = item.get("section", "Unknown")
            status = "PASS" if item.get("matched") else "FAIL"
            question = item.get("question", "")
            answer = item.get("answer", "")
            agent = item.get("agent", "unknown")
            citations = item.get("citations", [])
            expected_source = next((qa["expected_source"] for qa in QA_PAIRS if qa["id"] == q_id), "")

            f.write("=" * 80 + "\n")
            f.write(f"Q{q_id:03d} [{section}] {status}\n")
            f.write(f"Question: {question}\n")
            f.write(f"Expected: {next((qa['expected_answer'] for qa in QA_PAIRS if qa['id'] == q_id), '')}\n")
            f.write(f"Expected Source: {expected_source}\n")
            f.write(f"Answer: {answer}\n")
            f.write(f"Agent: {agent}\n")
            f.write(f"Citations: {citations}\n")

        f.write("=" * 80 + "\n")
        f.write("FINAL RESULTS\n")
        f.write("=" * 80 + "\n")
        f.write(f"{'Section':<15} {'Score':<10} {'Percentage'}\n")
        f.write("-" * 40 + "\n")
        for section, scores in section_scores.items():
            if scores["total"] > 0:
                pct = scores["correct"] / scores["total"] * 100
                f.write(f"{section:<15} {scores['correct']}/{scores['total']:<8} {pct:.1f}%\n")
        f.write("-" * 40 + "\n")
        overall_pct = total_correct / total_questions * 100 if total_questions > 0 else 0
        f.write(f"{'TOTAL':<15} {total_correct}/{total_questions:<8} {overall_pct:.1f}%\n")

    # Save summary-only txt
    summary_txt_path = OUTPUT_DIR / "150QmasterCraftsmanAutomation_summary.txt"
    with open(summary_txt_path, "w", encoding="utf-8") as f:
        f.write(f"{'Section':<15} {'Score':<10} {'Percentage'}\n")
        f.write("-" * 40 + "\n")
        for section, scores in section_scores.items():
            if scores["total"] > 0:
                pct = scores["correct"] / scores["total"] * 100
                f.write(f"{section:<15} {scores['correct']}/{scores['total']:<8} {pct:.1f}%\n")
        f.write("-" * 40 + "\n")
        overall_pct = total_correct / total_questions * 100 if total_questions > 0 else 0
        f.write(f"{'TOTAL':<15} {total_correct}/{total_questions:<8} {overall_pct:.1f}%\n")

    print(f"\nDetailed results saved to: {json_path}")
    print(f"Full text results saved to: {results_txt_path}")
    print(f"Summary text saved to: {summary_txt_path}")


if __name__ == "__main__":
    run_test()