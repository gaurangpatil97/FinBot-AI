import os, fitz
pdf_path = r'd:\FinBot\backend\data\uploads\craftsman_automation_ltd\pdf\Annual-Report-2023-24.pdf'
out_dir = r'd:\FinBot\scratch\fy24_pages'
os.makedirs(out_dir, exist_ok=True)
doc = fitz.open(pdf_path)
for i, page in enumerate(doc, start=1):
    pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
    img_path = os.path.join(out_dir, f'page_{i}.png')
    pix.save(img_path)
print(f'Saved {len(doc)} pages to {out_dir}')
