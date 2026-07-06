import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

chunks = [
    {
        "content": """Note 37 - Related Party Disclosures - Year ended March 31, 2025 vs March 31, 2024 (₹ in Million)
CSR Expenditure - Astral Foundation: FY25 = 126; FY24 = 108
Interest Income - Seal IT Services Limited, UK: FY25 = 43; FY24 = 19
Investment in Subsidiaries - Astral Coatings Private Limited: FY24 = 2,773 (no FY25 figure)
Redemption of debentures - Astral Coatings Private Limited: FY24 = 1,940 (no FY25 figure)
Purchase of Goods/Services - Kairamya Journeys LLP: FY25 = 141; FY24 = 130
Reimbursement of expenses claimed - Astral Coatings Private Limited: FY25 = 60; FY24 = 49
Remuneration - Sandeep Engineer: FY25 = 152; FY24 = 139
Remuneration - Hiranand Savlani: FY25 = 59; FY24 = 42
Remuneration - Others: FY25 = 57; FY24 = 52
Rent Paid - Jagruti Sandeep Engineer: FY25 = 1; FY24 = 1
Rent Paid - Sandeep Engineer HUF: FY25 = 1; FY24 = 1
Sale of Goods - Astral Coatings Private Limited: FY25 = 19; FY24 = 19
Sitting Fees to Independent Directors: 0-1 each
Loans Given - Seal IT Services Limited, UK: FY25 = 477; FY24 = 91
Loans Repaid - Astral Coatings Private Limited: FY24 = 8 (no FY25 figure)
Year-end balances (March 31, 2025):
Loans Given outstanding - Seal IT Services Limited, UK: 876 (FY24: 377)
Interest accrued on loan: 20 (FY24: 5)
Payables - Sandeep Engineer: 47 (FY24: 45)
Payables - Others: 5 (FY24: 4)
Advance for purchase of non-current investment - Astral Pipes Limited: 109 (FY24: 109)
Compensation of Key Management Personnel (short-term benefits): ₹251 Million (FY24: ₹216 Million)""",
        "filename": "Astral_Ltd_AR_FY2025_AnnualReport.pdf",
        "page": 104,
        "company": "astral_ltd"
    },
    {
        "content": """Note 33 - Contingent Liabilities and Commitments Not Provided For - As at March 31, 2025 (March 31, 2024) (₹ in Million)
Contingent Liabilities:
In respect of Income Tax: ₹16 (₹16)
In respect of Goods and Service Tax (GST), Customs Duty, Entry Tax, Value Added Tax and Central Sales Tax: ₹74 (₹11)
Commitments (separately listed, not contingent liabilities):
Capital Contracts remaining to be executed (Net of Advances): ₹1,845 (₹1,917)
Letters of Credit for Purchases: ₹334 (₹1,164)""",
        "filename": "Astral_Ltd_AR_FY2025_AnnualReport.pdf",
        "page": 91,
        "company": "astral_ltd"
    },
    {
        "content": """Note 30 - Other Expenses - Year ended March 31, 2025 vs March 31, 2024 (₹ in Million)
Top three largest line items:
Advertisement and Sales Promotions expenses: FY25 = 1,921; FY24 = 2,197 (decrease of 276)
Freight and Forwarding: FY25 = 1,507; FY24 = 1,357 (increase of 150)
Power and Fuel: FY25 = 1,279; FY24 = 1,268 (increase of 11)
Total Other Expenses: FY25 = 7,801; FY24 = 7,661""",
        "filename": "Astral_Ltd_AR_FY2025_AnnualReport.pdf",
        "page": 131,
        "company": "astral_ltd"
    },
    {
        "content": """Note 16 - Provisions - As at March 31, 2025 (March 31, 2024) (₹ in Million)
Non-current - Provision for Employee Benefits: 82 (50)
Current - Provision for Employee Benefits: 18 (7)
Note: only opening/closing balances are disclosed; no breakup showing amounts created, reversed, or utilized during the year is provided in this annual report.""",
        "filename": "Astral_Ltd_AR_FY2025_AnnualReport.pdf",
        "page": 166,
        "company": "astral_ltd"
    },
    {
        "content": """Related Party Transactions - Year 2024-25 vs 2023-24 (₹ in Lakhs)
Purchase of Goods & Services - Subsidiaries: FY24-25 = 47; FY23-24 = 70
Purchase of Goods & Services - Joint Ventures: FY24-25 = 501; FY23-24 = 489
Sale of Goods & Services - Subsidiaries: FY24-25 = 19,304; FY23-24 = 2,150
Sale of Goods & Services - Joint Ventures: FY24-25 = 5,916; FY23-24 = 5,597
Reimbursement of Expenditure to Subsidiaries: FY24-25 = 393; FY23-24 = Nil
Reimbursement of Expenditure from Subsidiaries: FY24-25 = 361; FY23-24 = Nil
Remuneration to Key Management Personnel: FY24-25 = 989; FY23-24 = 692
Commission to KMP: FY24-25 = 149; FY23-24 = 1,000
Sitting Fee: FY24-25 = 27; FY23-24 = 22
Interest Income from Subsidiaries: FY24-25 = 346; FY23-24 = Nil
Rental income - Subsidiaries: FY24-25 = 67; FY23-24 = 4
Rental income - Joint Ventures: FY24-25 = 2; FY23-24 = 2
Management Services Income - Subsidiaries: FY24-25 = 1,000; FY23-24 = Nil
Significant counterparties named: Carl Stahl Craftsman Enterprises Private Limited, Craftsman Europe BV-Netherlands, DR Axion India Private Limited, Sunbeam Lightweighting Solutions Private Limited
Sale of Goods & Services to DR Axion India Private Limited: ₹12,941 Lakhs
Sale of Goods & Services to Sunbeam Lightweighting Solutions Private Limited: ₹4,964 Lakhs
Year-end balances (March 31, 2025): Trade Receivables from Subsidiaries ₹888, from Joint Ventures ₹983; Trade Payables to Subsidiaries ₹268; Loans Receivable from Subsidiaries ₹6,640 (marked with *); Remuneration payable to KMP ₹15""",
        "filename": "Annual-Report-2025.pdf",
        "page": 233,
        "company": "craftsman_automation_ltd"
    },
    {
        "content": """Contingent Liabilities - As at March 31, 2025 (March 31, 2024) (₹ in Lakhs)
a. Claims against the Company not acknowledged as debt:
Excise Duty: 7 (7)
Service tax: 104 (67)
Goods and Service Tax: 1,952 (16)
Income tax: 307 (823)
b. Sales Bills discounted: 8,646 (4,617)
Commitments:
Commitment on capital account not provided as on March 31, 2025: ₹40,548 Lakhs (₹25,144 Lakhs as at March 31, 2024)""",
        "filename": "Annual-Report-2025.pdf",
        "page": 167,
        "company": "craftsman_automation_ltd"
    },
    {
        "content": """Standalone Segment Profit or Loss - Year 2024-25 vs 2023-24 (₹ in Lakhs)
Powertrain: FY24-25 = 24,857; FY23-24 = 29,163
Aluminium Products: FY24-25 = 11,600; FY23-24 = 12,902
Industrial & Engineering: FY24-25 = 1,717; FY23-24 = 4,673
Others: FY24-25 = 248; FY23-24 = Nil
Total Segments: FY24-25 = 38,422; FY23-24 = 46,738

Segment Assets - As at March 31, 2025 (March 31, 2024) (₹ in Lakhs)
Powertrain: 1,76,711 (1,54,572)
Aluminium Products: 1,66,955 (1,09,219)
Industrial & Engineering: 1,09,880 (86,324)
Total Segments: 4,53,546 (3,50,115)

Segment Liabilities - As at March 31, 2025 (March 31, 2024) (₹ in Lakhs)
Powertrain: 1,01,851 (94,667)
Aluminium Products: 1,24,967 (59,650)
Industrial & Engineering: 72,432 (59,106)
Total Segments: 2,99,250 (2,13,423)
Note: Segment Profit or Loss, Segment Assets, and Segment Liabilities are disclosed, but "segment-wise capital employed" is not separately disclosed as a distinct line item.""",
        "filename": "Annual-Report-2025.pdf",
        "page": 172,
        "company": "craftsman_automation_ltd"
    },
    {
        "content": """Note 2.7 - Other Expenses - Year 2024-25 vs 2023-24 (₹ in Lakhs)
Top three largest line items:
Stores, Spares & tool consumed: FY24-25 = 24,796; FY23-24 = 20,696 (increase of 4,100)
Power & Fuel: FY24-25 = 21,548; FY23-24 = 17,710 (increase of 3,838)
Payment to contractors: FY24-25 = 8,441; FY23-24 = 5,849 (increase of 2,592)
Total Other Expenses: FY24-25 = 88,833; FY23-24 = 72,243""",
        "filename": "Annual-Report-2025.pdf",
        "page": 238,
        "company": "craftsman_automation_ltd"
    },
    {
        "content": """Standalone Short Term Provisions (Note 1.32) - As at March 31, 2025 (March 31, 2024) (₹ in Lakhs)
Provision for employee benefits - Gratuity: 630 (505)
Other Provisions - Provision for Warranty Cost: 280 (230)
Other Provisions - Provision for Rejection: 160 (127)
Total: 1,070 (862)
Movement in Provision for product warranties (FY2024-25): Opening 230, Expired during the year 230, Warranty provided for current year 280, Closing 280
Movement in Provision for Rejection (FY2024-25): Opening 127, Expired during the year 127, Rejection provided for current year 160, Closing 160
Note 2.7 Other Expenses discloses Provisions charged during the year: Warranty 45 (41 in FY23-24), Rejections 34 (-3 in FY23-24), Doubtful debts 933 (-94 in FY23-24)""",
        "filename": "Annual-Report-2025.pdf",
        "page": 145,
        "company": "craftsman_automation_ltd"
    }
]

base_path = "D:/FinBot/backend/data/uploads"

for c in chunks:
    source_path = os.path.join(base_path, c["company"], "pdf", c["filename"])
    if not os.path.exists(source_path):
        print(f"ERROR: Source file does not exist: {source_path}")
    
    metadata = {
        "filename": c["filename"],
        "page": c["page"],
        "source": source_path,
        "chunk_type": "manual_table",
        "chunk_index": 0
    }
    print(f"\n--- CHUNK DRY RUN ---")
    print(f"Company: {c['company']}")
    print(f"Metadata: {metadata}")
    print(f"Content:\n{c['content']}")
