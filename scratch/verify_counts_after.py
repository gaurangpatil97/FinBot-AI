import os
import sys
import chromadb
from pprint import pprint

sys.stdout.reconfigure(encoding='utf-8')

CHROMA_STORE = "D:/FinBot/backend/chroma_store"

def get_stats(company, collection_name, page, filename):
    db_path = os.path.join(CHROMA_STORE, company, "pdf")
    client = chromadb.PersistentClient(path=db_path)
    col = client.get_collection(collection_name)
    
    total_count = col.count()
    
    manual = col.get(where={"chunk_type": "manual_table"})
    manual_count = len(manual['ids']) if manual and manual.get('ids') else 0
    
    original = col.get(where={"$and": [{"filename": filename}, {"page": page}, {"chunk_type": "text"}]})
    original_count = len(original['ids']) if original and original.get('ids') else 0
    
    return {
        "total": total_count,
        "manual_count": manual_count,
        "original_count": original_count
    }

print("=== AFTER INSERTION DB STATS ===")
astral = get_stats("astral_ltd", "astral_ltd_pdf_text", 208, "Astral_Ltd_AR_FY2025_AnnualReport.pdf")
craftsman = get_stats("craftsman_automation_ltd", "craftsman_automation_ltd_pdf_text", 93, "7.-Annual-Report-2021-22.pdf")

print(f"Astral Total: {astral['total']} (Manual: {astral['manual_count']}, Original Page 208: {astral['original_count']} chunks)")
print(f"Craftsman Total: {craftsman['total']} (Manual: {craftsman['manual_count']}, Original Page 93: {craftsman['original_count']} chunks)")
