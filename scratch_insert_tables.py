import os
import sys
import pdfplumber
import chromadb
from pathlib import Path

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import backend modules
sys.path.append(os.path.abspath("d:/FinBot/backend"))
# from app.core.embedder import generate_embeddings

# Target pages to process
ASTRAL_PDF = r"D:\FinBot\backend\data\uploads\astral_ltd\pdf\Astral_Ltd_AR_FY2025_AnnualReport.pdf"
CRAFTSMAN_PDF = r"D:\FinBot\backend\data\uploads\craftsman_automation_ltd\pdf\7.-Annual-Report-2021-22.pdf"

TARGETS = [
    # Astral targets
    ("astral_ltd", ASTRAL_PDF, 91),
    ("astral_ltd", ASTRAL_PDF, 94),
    ("astral_ltd", ASTRAL_PDF, 110),
    ("astral_ltd", ASTRAL_PDF, 131),
    ("astral_ltd", ASTRAL_PDF, 159),
    ("astral_ltd", ASTRAL_PDF, 161),
    ("astral_ltd", ASTRAL_PDF, 164),
    ("astral_ltd", ASTRAL_PDF, 166),
    ("astral_ltd", ASTRAL_PDF, 173),
    ("astral_ltd", ASTRAL_PDF, 196),
    ("astral_ltd", ASTRAL_PDF, 197),
    ("astral_ltd", ASTRAL_PDF, 208),
    ("astral_ltd", ASTRAL_PDF, 209),
    
    # Craftsman targets
    ("craftsman_automation_ltd", CRAFTSMAN_PDF, 93),
    ("craftsman_automation_ltd", CRAFTSMAN_PDF, 164),
    ("craftsman_automation_ltd", CRAFTSMAN_PDF, 167),
    ("craftsman_automation_ltd", CRAFTSMAN_PDF, 171),
    ("craftsman_automation_ltd", CRAFTSMAN_PDF, 172),
    ("craftsman_automation_ltd", CRAFTSMAN_PDF, 222),
    ("craftsman_automation_ltd", CRAFTSMAN_PDF, 232),
    ("craftsman_automation_ltd", CRAFTSMAN_PDF, 233),
    ("craftsman_automation_ltd", CRAFTSMAN_PDF, 238),
    ("craftsman_automation_ltd", CRAFTSMAN_PDF, 239)
]

def format_table(table):
    lines = []
    for row in table:
        clean_row = [str(cell).replace('\\n', ' ').replace('\n', ' ') if cell is not None else '' for cell in row]
        lines.append(" | ".join(clean_row))
    return "\n".join(lines)

def run_extraction(dry_run=True):
    print(f"Starting {'DRY RUN' if dry_run else 'ACTUAL INSERTION'}...")
    total_pages = 0
    total_tables_found = 0
    
    chunks_to_insert = {
        "astral_ltd": [],
        "craftsman_automation_ltd": []
    }

    # Group by PDF to avoid reopening repeatedly
    by_pdf = {}
    for company, pdf_path, page_num in TARGETS:
        if pdf_path not in by_pdf:
            by_pdf[pdf_path] = []
        by_pdf[pdf_path].append((company, page_num))

    for pdf_path, page_list in by_pdf.items():
        filename = Path(pdf_path).name
        print(f"\nOpening {filename}...")
        with pdfplumber.open(pdf_path) as pdf:
            for company, page_num in page_list:
                total_pages += 1
                page_idx = page_num - 1
                page = pdf.pages[page_idx]
                
                tables = page.extract_tables()
                
                if not tables:
                    print(f"[!] WARNING: NO tables found on page {page_num} of {filename}!")
                    continue
                
                print(f"[*] Found {len(tables)} tables on page {page_num} of {filename}")
                total_tables_found += len(tables)
                
                for i, table in enumerate(tables):
                    formatted_text = format_table(table)
                    chunk_content = f"[TABLE_DATA_PAGE_{page_num}_TABLE_{i+1}]\n{formatted_text}"
                    
                    if dry_run:
                        print(f"\n--- DRy RUN TABLE TEXT (Page {page_num}, Table {i+1}) ---")
                        print(chunk_content[:250] + ("..." if len(chunk_content) > 250 else ""))
                        print("--------------------------------------------------\n")
                    
                    chunks_to_insert[company].append({
                        "content": chunk_content,
                        "metadata": {
                            "filename": filename,
                            "page": page_num,
                            "source": str(pdf_path),
                            "chunk_type": "table"
                        }
                    })

    print(f"\n--- DRY RUN SUMMARY ---")
    print(f"Target pages processed: {total_pages}")
    print(f"Total tables found: {total_tables_found}")
    print("Zero existing chunks will be modified or deleted. We only use `collection.add()`.")

if __name__ == "__main__":
    run_extraction(dry_run=True)
