import sys
import os
from pathlib import Path

import fitz
import json
from app.core.pdf_processor import describe_image
from app.core.chunker import chunk_documents
from app.core.embedder import generate_embeddings
from app.db.vector_store import get_or_create_collection, store_chunks
from config import settings

targets = [
    {
        "filename": "7.-Annual-Report-2021-22.pdf",
        "page_display": 19,
        "year": "FY22"
    },
    {
        "filename": "Annual-Report_2023.pdf",
        "page_display": 21,
        "year": "FY23"
    },
    {
        "filename": "Annual-Report-2023-24.pdf",
        "page_display": 21,
        "year": "FY24"
    }
]

company_slug = "craftsman_automation_ltd"
pdf_dir = "/app/data/uploads/craftsman_automation_ltd/pdf/"
tmp_dir = settings.TMP_DIR
os.makedirs(tmp_dir, exist_ok=True)

collection_name = f"{company_slug}_images"
chroma_path = str(Path(settings.CHROMA_BASE_DIR) / company_slug / "images")

coll = get_or_create_collection(collection_name, chroma_path=chroma_path)
print(f"Starting chunk count: {coll.count()}")

pages_data = []

for target in targets:
    filename = target["filename"]
    page_display_num = target["page_display"]
    year = target["year"]
    
    file_path = os.path.join(pdf_dir, filename)
    doc_fitz = fitz.open(file_path)
    page_num = page_display_num - 1
    page_fitz = doc_fitz[page_num]
    
    matrix = fitz.Matrix(300 / 72, 300 / 72)
    pix = page_fitz.get_pixmap(matrix=matrix)

    if pix.colorspace and pix.colorspace != fitz.csRGB:
        pix = fitz.Pixmap(fitz.csRGB, pix)

    img_path = f"{tmp_dir}/page_{page_display_num}_{year}.png"
    pix.save(img_path)
    
    print(f"Extracting description for {filename} Page {page_display_num}...")
    description = describe_image(img_path, page_display_num)
    
    try:
        os.remove(img_path)
    except:
        pass
        
    pages_data.append({
        "content": f"[IMAGE CONTENT - Page {page_display_num}]\n{description}",
        "metadata": {
            "filename": filename,
            "page": page_display_num,
            "source": file_path,
            "chunk_type": "image",
            "company_slug": company_slug,
            "year": year
        }
    })

print(f"Embedding {len(pages_data)} new chunks...")
chunks = chunk_documents(pages_data)
chunks = generate_embeddings(chunks)
store_chunks(chunks, collection_name, chroma_path=chroma_path)

print(f"Ending chunk count: {coll.count()}")
