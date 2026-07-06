import fitz, re, os

pdf_path = r'd:/FinBot/backend/data/uploads/craftsman_automation_ltd/pdf/Annual-Report-2025.pdf'
search_terms = [
    r'Excluding\s+Excise\s+Duty',
    r'Revenue CAGR',
]

doc = fitz.open(pdf_path)
found = False
for page_num in range(len(doc)):
    text = doc[page_num].get_text()
    if any(re.search(term, text, re.IGNORECASE) for term in search_terms):
        snippet = '\n'.join(text.splitlines()[:5])
        print(f"--- Page {page_num+1} ---")
        print(snippet)
        found = True
print('FOUND' if found else 'NOT FOUND')
