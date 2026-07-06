import fitz, json, os
pdf_path = r'd:\FinBot\backend\data\uploads\craftsman_automation_ltd\pdf\Annual-Report-2023-24.pdf'
out = []
doc = fitz.open(pdf_path)
for i, page in enumerate(doc, start=1):
    txt = page.get_text()
    if 'Debt/EBITDA' in txt or 'Debt‑EBITDA' in txt:
        out.append({'page': i, 'snippet': txt[:200]})
print(json.dumps(out, indent=2))
