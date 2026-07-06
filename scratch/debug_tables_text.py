import pdfplumber
import os
import pprint
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = "D:/FinBot/backend/data/uploads"

def debug_page(company, filename, page_num):
    filepath = os.path.join(BASE_DIR, company, "pdf", filename)
    print(f"\n{'='*50}\nDebugging {filename} - Page {page_num}\n{'='*50}")
    
    with pdfplumber.open(filepath) as pdf:
        page = pdf.pages[page_num - 1]
        tables = page.extract_tables(table_settings={"vertical_strategy": "text", "horizontal_strategy": "text"})
        
        print(f"Total tables detected: {len(tables)}\n")
        
        for i, table in enumerate(tables):
            print(f"--- Table {i+1} Raw List-of-Lists ---")
            pprint.pprint(table)
            print("\n")

if __name__ == "__main__":
    debug_page("astral_ltd", "Astral_Ltd_AR_FY2025_AnnualReport.pdf", 208)
    debug_page("craftsman_automation_ltd", "7.-Annual-Report-2021-22.pdf", 93)
