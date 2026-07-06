import pdfplumber
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

astral_pdf_path = r"D:\FinBot\backend\data\uploads\astral_ltd\pdf\Astral_Ltd_AR_FY2025_AnnualReport.pdf"
craftsman_pdf_path = r"D:\FinBot\backend\data\uploads\craftsman_automation_ltd\pdf\7.-Annual-Report-2021-22.pdf"

def extract_pdf_page(pdf_path, page_num_1_indexed):
    print(f"\n=========================================")
    filename = pdf_path.split('\\')[-1]
    print(f"Extracting {filename} - Page {page_num_1_indexed}")
    print(f"=========================================\n")
    
    with pdfplumber.open(pdf_path) as pdf:
        page_index = page_num_1_indexed - 1
        page = pdf.pages[page_index]
        
        # Method 1: Bisection
        width = page.width
        left = page.within_bbox((0, 0, width/2, page.height))
        right = page.within_bbox((width/2, 0, width, page.height))
        left_text = left.extract_text() or ""
        right_text = right.extract_text() or ""
        text = left_text + "\n" + right_text
        
        print("--- CURRENT BISECTION TEXT EXTRACTION ---")
        print(text.strip())
        print("\n-----------------------------------------\n")
        
        # Method 2: Table extraction
        tables = page.extract_tables()
        print("--- PROPER TABLE EXTRACTION ---")
        for i, table in enumerate(tables):
            print(f"Table {i+1}:")
            for row in table:
                # Clean up None values and format
                clean_row = [str(cell).replace('\n', ' ') if cell is not None else '' for cell in row]
                print(" | ".join(clean_row))
            print()
        print("-----------------------------------------\n")

extract_pdf_page(astral_pdf_path, 208)
extract_pdf_page(craftsman_pdf_path, 93)
