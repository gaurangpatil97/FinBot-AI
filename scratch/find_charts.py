import fitz
import os

pdf_dir = "d:/FinBot/backend/data/uploads/craftsman_automation_ltd/pdf/"
files = [
    "7.-Annual-Report-2021-22.pdf",
    "Annual-Report_2023.pdf",
    "Annual-Report-2023-24.pdf"
]

for f in files:
    path = os.path.join(pdf_dir, f)
    print(f"\n{'='*50}\nSearching in {f}\n{'='*50}")
    try:
        doc = fitz.open(path)
        for i in range(min(30, len(doc))):
            text = doc[i].get_text()
            lower_text = text.lower()
            if any(term in lower_text for term in ["kpi", "position", "debt", "ebitda", "over the years", "performance", "consolidated"]):
                print(f"--- Page {i+1} ---")
                # print a snippet
                snippet = " ".join(text.replace('\n', ' ').split())
                print(snippet[:500] + "...")
    except Exception as e:
        print(f"Error reading {f}: {e}")
