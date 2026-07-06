import os
import chromadb

CHROMA_STORE = "D:/FinBot/backend/chroma_store"

def query_direct():
    db_path = os.path.join(CHROMA_STORE, "astral_ltd", "pdf")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection("astral_ltd_pdf_text")
    
    q = "In Note 37 (Segment Reporting), the Group reports segment revenues and profits for 'Plastic' and 'Adhesives'. Show how the total segment profit reconciles to the Consolidated Profit Before Tax of ₹6,485 million"
    
    sys.path.append("D:/FinBot/backend")
    from app.core.embedder import generate_embeddings
    
    chunk = {"content": q, "metadata": {}}
    embedded = generate_embeddings([chunk])
    
    res = collection.query(
        query_embeddings=[embedded[0]["embedding"]],
        n_results=15
    )
    
    for i, meta in enumerate(res["metadatas"][0]):
        print(f"{i+1}. {meta.get('filename')} - Page {meta.get('page')} (Type: {meta.get('chunk_type')}) - Dist: {res['distances'][0][i]}")
        if meta.get('chunk_type') == 'manual_table':
            print("   ->", res["documents"][0][i][:200].replace('\n', ' '))

if __name__ == "__main__":
    import sys
    query_direct()
