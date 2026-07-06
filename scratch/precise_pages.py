import fitz
import os

pdf_dir = "d:/FinBot/backend/data/uploads/craftsman_automation_ltd/pdf/"
files = [
    "7.-Annual-Report-2021-22.pdf",
    "Annual-Report_2023.pdf"
]

for f in files:
    path = os.path.join(pdf_dir, f)
    print(f"\n==================== {f} ====================")
    try:
        doc = fitz.open(path)
        for i in range(15, 26):
            if i < len(doc):
                text = doc[i].get_text().lower()
                if any(t in text for t in ["debt-ebitda", "debt-equity", "kpi"]):
                    print(f"Page {i+1}: matches keywords!")
    except Exception as e:
        print(e)
