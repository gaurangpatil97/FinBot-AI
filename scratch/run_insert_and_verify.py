import sys
import os
import chromadb
from pprint import pprint

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append("D:/FinBot/scratch")

from manual_table_insert import process_manual_tables

CHROMA_STORE = "D:/FinBot/backend/chroma_store"

def get_stats(company, collection_name, page, filename):
    db_path = os.path.join(CHROMA_STORE, company, "pdf")
    client = chromadb.PersistentClient(path=db_path)
    col = client.get_collection(collection_name)
    
    total_count = col.count()
    
    # check manual_table chunks
    manual = col.get(where={"chunk_type": "manual_table"})
    manual_count = len(manual['ids']) if manual and manual.get('ids') else 0
    
    # check original chunk for the specific page
    original = col.get(where={"$and": [{"filename": filename}, {"page": page}, {"chunk_type": "text"}]})
    original_count = len(original['ids']) if original and original.get('ids') else 0
    
    return {
        "total": total_count,
        "manual_count": manual_count,
        "original_count": original_count,
        "original_ids": original['ids'] if original else []
    }

print("=== BEFORE INSERTION ===")
astral_before = get_stats("astral_ltd", "astral_ltd_pdf_text", 208, "Astral_Ltd_AR_FY2025_AnnualReport.pdf")
craftsman_before = get_stats("craftsman_automation_ltd", "craftsman_automation_ltd_pdf_text", 93, "7.-Annual-Report-2021-22.pdf")

print(f"Astral Total: {astral_before['total']}, Manual: {astral_before['manual_count']}, Original Page 208: {astral_before['original_count']} chunks")
print(f"Craftsman Total: {craftsman_before['total']}, Manual: {craftsman_before['manual_count']}, Original Page 93: {craftsman_before['original_count']} chunks")

print("\n=== RUNNING INSERTION ===")
# execute insertion
process_manual_tables(dry_run=False)

print("\n=== AFTER INSERTION ===")
astral_after = get_stats("astral_ltd", "astral_ltd_pdf_text", 208, "Astral_Ltd_AR_FY2025_AnnualReport.pdf")
craftsman_after = get_stats("craftsman_automation_ltd", "craftsman_automation_ltd_pdf_text", 93, "7.-Annual-Report-2021-22.pdf")

print(f"Astral Total: {astral_after['total']} (Diff: {astral_after['total'] - astral_before['total']})")
print(f"Astral Manual: {astral_after['manual_count']}")
print(f"Astral Original Page 208: {astral_after['original_count']} chunks (Unchanged? {astral_after['original_count'] == astral_before['original_count'] and astral_after['original_ids'] == astral_before['original_ids']})")

print(f"\nCraftsman Total: {craftsman_after['total']} (Diff: {craftsman_after['total'] - craftsman_before['total']})")
print(f"Craftsman Manual: {craftsman_after['manual_count']}")
print(f"Craftsman Original Page 93: {craftsman_after['original_count']} chunks (Unchanged? {craftsman_after['original_count'] == craftsman_before['original_count'] and craftsman_after['original_ids'] == craftsman_before['original_ids']})")
