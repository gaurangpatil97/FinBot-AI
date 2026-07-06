import fitz
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf_path = 'D:/FinBot/backend/data/uploads/astral_ltd/pdf/Astral_Ltd_AR_FY2022_AnnualReport.pdf'
doc = fitz.open(pdf_path)
page = doc[170]
print(page.get_text())
doc.close()
