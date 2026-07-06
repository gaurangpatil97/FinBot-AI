import os
import sys
import chromadb
import hashlib

sys.stdout.reconfigure(encoding='utf-8')

ASTRAL_CONTENT = """Note 37 - Segment Reporting - Year ended March 31, 2022 vs March 31, 2021 (₹ in Million)
The Group's business segments are "Plastic" and "Adhesives".

Segment Revenue:
Plastic: FY22 = 33,658; FY21 = 24,187
Adhesives: FY22 = 10,282; FY21 = 7,576
Total Segment Revenue: FY22 = 43,940; FY21 = 31,763

Segment Profit:
Plastic: FY22 = 5,200; FY21 = 4,194
Adhesives: FY22 = 1,254; FY21 = 1,145
Total Segment Profit: FY22 = 6,454; FY21 = 5,339

Reconciliation of FY22 Segment Profit to FY22 Consolidated Profit Before Tax (PBT):
Total Segment Profit (FY22): 6,454
Less: Other Unallocable expenses: (89)
Less: Finance costs: (129)
Add: Unallocable Non-operating Income: 268
Less: Share of loss of joint venture: (19)
Consolidated Profit Before Tax (PBT) FY22: 6,485
(6,454 - 89 - 129 + 268 - 19 = 6,485)"""

CHROMA_STORE = "D:/FinBot/backend/chroma_store"

def insert_chunk():
    db_path = os.path.join(CHROMA_STORE, "astral_ltd", "pdf")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection("astral_ltd_pdf_text")
    
    source_path = "D:\\FinBot\\backend\\data\\uploads\\astral_ltd\\pdf\\Astral_Ltd_AR_FY2022_AnnualReport.pdf"
    
    # 3. Embed new chunk
    sys.path.append("D:/FinBot/backend")
    from app.core.embedder import generate_embeddings
    
    chunk = {
        "content": ASTRAL_CONTENT,
        "metadata": {
            "filename": "Astral_Ltd_AR_FY2022_AnnualReport.pdf",
            "page": 189,
            "source": source_path,
            "chunk_type": "manual_table",
            "chunk_index": 0
        }
    }
    
    print("\nEmbedding new chunk...")
    embedded_chunks = generate_embeddings([chunk])
    
    content_hash = hashlib.md5(ASTRAL_CONTENT.encode("utf-8")).hexdigest()
    doc_id = f"manual_table_Astral_Ltd_AR_FY2022_AnnualReport.pdf_189_{content_hash[:8]}"
    
    collection.add(
        ids=[doc_id],
        documents=[embedded_chunks[0]["content"]],
        embeddings=[embedded_chunks[0]["embedding"]],
        metadatas=[embedded_chunks[0]["metadata"]]
    )
    print(f"Inserted new chunk {doc_id} successfully.")

if __name__ == "__main__":
    insert_chunk()
