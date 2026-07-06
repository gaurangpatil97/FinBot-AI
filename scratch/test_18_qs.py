import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

# The exact target questions to ask
TARGETS = {
    # target 10 questions
    "astral_ltd P3": "In Note 30, what were the top three largest line items under 'Other Expenses' for FY25, and how much did each change compared to FY24?",
    "astral_ltd P4": "In Note 16, provide the opening and closing balances for short-term/current and long-term/non-current provision for employee benefits. Detail the amounts created, reversed, or utilized during the year.",
    "astral_ltd P7": "In Note 37 (Segment Reporting), what was the total segment profit for 'Plumbing' and 'Paints and Adhesives' in FY22 compared to FY21?",
    "astral_ltd P8": "In Note 33, what are the total Contingent Liabilities in respect of Income Tax and GST for FY25 compared to FY24?",
    "astral_ltd P10": "In Note 37 (Related Party Disclosures), how much did the company spend on CSR activities through the Astral Foundation in FY25, and what was the balance of loans given to Seal IT Services Limited, UK, at the end of the year?",
    
    "craftsman_automation_ltd P3": "In Note 2.7, what were the top three largest line items under 'Other Expenses' for FY24-25, and how much did each change compared to FY23-24?",
    "craftsman_automation_ltd P4": "In Note 1.32, provide the opening and closing balances for short-term/current and long-term/non-current provision for employee benefits. Detail the amounts created, reversed, or utilized during the year.",
    "craftsman_automation_ltd P7": "In the Standalone Segment Reporting note, what were the segment assets and segment liabilities for 'Aluminium Products' in FY24-25 compared to FY23-24?",
    "craftsman_automation_ltd P8": "In the Contingent Liabilities note, what are the total Contingent Liabilities in respect of Income Tax and GST for FY25 compared to FY24?",
    "craftsman_automation_ltd P10": "In the Related Party Transactions note, how much was the total remuneration paid to Key Management Personnel in FY24-25, and what were the year-end balances of Trade Receivables from Joint Ventures?",

    # regression check questions
    "astral_ltd P1": "What is the company's total revenue from operations for the year ended March 31, 2025, and how does it compare to the previous year?",
    "astral_ltd P9": "What was the total remuneration paid to Key Management Personnel in FY25 compared to FY24?",
    "astral_ltd CP1": "Does the total comprehensive income for the year ended March 31, 2025, match the sum of profit after tax and other comprehensive income? Show the calculation.",
    "astral_ltd CP4": "In Note 37 (Segment Reporting), reconcile total segment profit for 'Plumbing' and 'Paints and Adhesives' to the Consolidated Profit Before Tax of ₹7,336 million, detailing each reconciling item.",
    "astral_ltd CP7": "In Note 37, reconcile total segment profit for 'Plumbing' and 'Paints and Adhesives' to the Consolidated Profit Before Tax of ₹7,025 million, detailing each reconciling item.",
    
    "craftsman_automation_ltd P9": "What was the total remuneration paid to Key Management Personnel in FY25 compared to FY24?",
    "craftsman_automation_ltd CP2": "What is the year-over-year percentage change in 'Purchase of stock-in-trade' for the year ended March 31, 2025, compared to the previous year? Show the calculation.",
    "craftsman_automation_ltd CP3": "Calculate the Interest Coverage Ratio (Profit Before Tax and Finance Costs / Finance Costs) for the year ended March 31, 2022, based on the Standalone Statement of Profit and Loss, and compare it with the ratio reported in the 'Ratio Analysis' section (page 93). Are they consistent?"
}

def main():
    for label, question in TARGETS.items():
        print(f"\n=============================================")
        print(f"--- {label} ---")
        print(f"Question: {question}")
        try:
            # Extract company slug from label
            company_slug = label.split(" ")[0]
            
            resp = requests.post(
                "http://localhost:8000/api/v1/query",
                json={
                    "question": question,
                    "company_slug": company_slug,
                    "session_id": "test_18"
                },
                timeout=60
            )
            if resp.status_code == 200:
                print("Answer:")
                print(resp.json()["answer"])
            else:
                print(f"Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    main()
