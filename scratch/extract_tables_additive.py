import os
import sys
import argparse
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')

TARGETS = [
    ("astral_ltd", "Astral_Ltd_AR_FY2025_AnnualReport.pdf", [29, 40, 49, 91, 94, 100, 104, 110, 122, 131, 143, 164, 166, 182, 197, 202, 203, 208, 209]),
    ("craftsman_automation_ltd", "7.-Annual-Report-2021-22.pdf", [93]),
    ("craftsman_automation_ltd", "Annual-Report-2025.pdf", [8, 10, 16, 19, 145, 164, 167, 172, 212, 222, 233, 238, 239])
]

BASE_DIR = "D:/FinBot/backend/data/uploads"

def format_table(table):
    formatted_rows = []
    for row in table:
        clean_row = [str(cell).replace('\n', ' ').strip() if cell is not None else "" for cell in row]
        # skip completely empty rows
        if any(clean_row):
            formatted_rows.append(" | ".join(clean_row))
    return "\n".join(formatted_rows)

def process_targets(dry_run=True):
    total_processed = 0
    pages_with_no_tables = []
    new_chunks = []
    
    for company, filename, pages in TARGETS:
        filepath = os.path.join(BASE_DIR, company, "pdf", filename)
        if not os.path.exists(filepath):
            print(f"ERROR: {filepath} not found!")
            continue
            
        print(f"\n================ Processing {filename} ================")
        with pdfplumber.open(filepath) as pdf:
            for page_num in pages:
                total_processed += 1
                if page_num - 1 >= len(pdf.pages):
                    print(f"  Page {page_num} is out of bounds for {filename}")
                    continue
                    
                page = pdf.pages[page_num - 1]
                tables = page.extract_tables()
                
                if not tables:
                    print(f"  [NO TABLES] Page {page_num} had NO tables detected!")
                    pages_with_no_tables.append((filename, page_num))
                    continue
                    
                print(f"  [SUCCESS] Page {page_num}: Found {len(tables)} tables")
                
                for i, table in enumerate(tables):
                    table_text = format_table(table)
                    if not table_text.strip():
                        continue
                        
                    chunk = {
                        "content": table_text,
                        "metadata": {
                            "filename": filename,
                            "page": page_num,
                            "source": filepath,
                            "chunk_type": "table",
                            "chunk_index": i
                        }
                    }
                    new_chunks.append((company, chunk))
                    
                    if dry_run:
                        print(f"    --- Table {i+1} snippet ---")
                        # print first 3 lines and last line
                        lines = table_text.split('\n')
                        if len(lines) <= 4:
                            print("\n".join(lines))
                        else:
                            print("\n".join(lines[:3]))
                            print("    ... (truncated) ...")
                            print(lines[-1])
                        print("")
                        
    if dry_run:
        print("\n=== DRY RUN SUMMARY ===")
        print(f"Target pages processed: {total_processed}")
        print(f"Total new table chunks generated: {len(new_chunks)}")
        print(f"Pages with NO tables detected: {len(pages_with_no_tables)}")
        if pages_with_no_tables:
            print(f"List of pages with no tables: {pages_with_no_tables}")
        print("Zero existing chunks in ChromaDB have been modified or deleted. (0 database writes made).")
    else:
        # Actual embedding and insertion
        import sys
        sys.path.append("D:/FinBot/backend")
        from app.core.embedder import generate_embeddings
        from app.db.vector_store import store_chunks
        
        # Group by company
        chunks_by_company = {}
        for comp, chunk in new_chunks:
            if comp not in chunks_by_company:
                chunks_by_company[comp] = []
            chunks_by_company[comp].append(chunk)
            
        for comp, chunks in chunks_by_company.items():
            print(f"Embedding {len(chunks)} chunks for {comp}...")
            embedded_chunks = generate_embeddings(chunks)
            collection_name = f"{comp}_pdf_text"
            print(f"Inserting into {collection_name}...")
            store_chunks(embedded_chunks, collection_name)
            
        print("Insertion complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--insert", action="store_true", help="Run actual insertion")
    args = parser.parse_args()
    
    dry_run = not args.insert
    process_targets(dry_run=dry_run)
