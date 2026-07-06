import fitz
import glob
import os

pdf_files = glob.glob('D:/FinBot/backend/data/uploads/astral_ltd/pdf/*.pdf')

for pdf_path in pdf_files:
    print(f"\nChecking {os.path.basename(pdf_path)}")
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            text = page.get_text()
            if text and '6,454' in text and 'Plastic' in text and '1,254' in text:
                print(f"  --> MATCH FOUND on PDF page index {i} (1-indexed page {i+1})")
                print("  Snippet of text:")
                print("-" * 40)
                print(text[:1000]) # print first 1000 chars
                print("-" * 40)
                break
        else:
            print("  No match found in this PDF.")
        doc.close()
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
