import os
import sys
import argparse
import chromadb

sys.stdout.reconfigure(encoding='utf-8')

ASTRAL_CONTENT = """Segment Reporting - Astral Ltd FY25 Annual Report, Page 208
Segment Reporting - Year ended March 31, 2025 vs March 31, 2024 (₹ in Million)

Segment Revenue:
Plumbing: FY25 = 41,963; FY24 = 41,420
Paints and Adhesives: FY25 = 16,361; FY24 = 14,994
Total Segment Revenue: FY25 = 58,324; FY24 = 56,414

Segment Profit:
Plumbing: FY25 = 6,126; FY24 = 6,054
Paints and Adhesives: FY25 = 1,150; FY24 = 1,396
Total Segment Profit: FY25 = 7,276; FY24 = 7,450

Reconciliation of FY25 Segment Profit to FY25 Consolidated Profit Before Tax (PBT):
Total Segment Profit (FY25): 7,276
Add: Unallocated Income/(Expenses) net: 162
Less: Finance costs: (413)
Less: Share of loss of joint venture: 0
Consolidated Profit Before Tax (PBT) FY25: 7,025
(7,276 + 162 - 413 + 0 = 7,025)

Reconciliation of FY24 Segment Profit to FY24 Consolidated Profit Before Tax (PBT):
Total Segment Profit (FY24): 7,450
Add: Unallocated Income/(Expenses) net: 178
Less: Finance costs: (291)
Less: Share of loss of joint venture: (1)
Consolidated Profit Before Tax (PBT) FY24: 7,336
(7,450 + 178 - 291 - 1 = 7,336)

Segment Assets as at March 31, 2025 (March 31, 2024):
Plumbing: 28,677 (24,623)
Paints and Adhesives: 15,603 (14,222)
Total Segment Assets: 44,280 (38,845)

Segment Liabilities as at March 31, 2025 (March 31, 2024):
Plumbing: 7,521 (7,657)
Paints and Adhesives: 3,432 (2,606)
Total Segment Liabilities: 10,953 (10,263)"""

CHROMA_STORE = "D:/FinBot/backend/chroma_store"

def fix_chunk():
    db_path = os.path.join(CHROMA_STORE, "astral_ltd", "pdf")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection("astral_ltd_pdf_text")
    
    # 1. Find existing
    results = collection.get(
        where={
            "$and": [
                {"chunk_type": "manual_table"},
                {"page": 208},
                {"filename": "Astral_Ltd_AR_FY2025_AnnualReport.pdf"}
            ]
        }
    )
    
    ids_to_delete = results.get("ids", [])
    print(f"Found {len(ids_to_delete)} chunks matching criteria to delete: {ids_to_delete}")
    
    if len(ids_to_delete) != 1:
        print("ERROR: Did not find exactly 1 chunk. Aborting!")
        return
        
    source_path = results.get("metadatas", [{}])[0].get("source", "D:\\FinBot\\backend\\data\\uploads\\astral_ltd\\pdf\\Astral_Ltd_AR_FY2025_AnnualReport.pdf")
    
    # 2. Delete
    collection.delete(ids=ids_to_delete)
    print("Deleted old chunk successfully.")
    
    # 3. Embed new chunk
    sys.path.append("D:/FinBot/backend")
    from app.core.embedder import generate_embeddings
    
    chunk = {
        "content": ASTRAL_CONTENT,
        "metadata": {
            "filename": "Astral_Ltd_AR_FY2025_AnnualReport.pdf",
            "page": 208,
            "source": source_path,
            "chunk_type": "manual_table",
            "chunk_index": 0
        }
    }
    
    print("\nEmbedding new chunk...")
    embedded_chunks = generate_embeddings([chunk])
    
    # 4. Insert
    # We must insert using the standard method so ID generation is consistent, but since we already have a client open we can just insert directly.
    # Wait, the ID generation in store_chunks is based on hashing the text or metadata.
    import hashlib
    # Let's just use store_chunks from vector_store, but it might fail because of the client issue we saw before.
    # We'll just insert it directly into the collection since it's only 1 chunk.
    # Generating ID like vector_store does:
    content_hash = hashlib.md5(ASTRAL_CONTENT.encode("utf-8")).hexdigest()
    doc_id = f"manual_table_Astral_Ltd_AR_FY2025_AnnualReport.pdf_208_{content_hash[:8]}"
    
    collection.add(
        ids=[doc_id],
        documents=[embedded_chunks[0]["content"]],
        embeddings=[embedded_chunks[0]["embedding"]],
        metadatas=[embedded_chunks[0]["metadata"]]
    )
    print(f"Inserted new chunk {doc_id} successfully.")

if __name__ == "__main__":
    fix_chunk()
