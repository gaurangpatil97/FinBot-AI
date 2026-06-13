import os
import sys

sys.path.append(os.path.abspath(r"D:\FinBot\backend"))

from app.db.vector_store import query_collection, get_or_create_collection
from app.core.embedder import generate_embeddings
from config import settings

company_slug = "craftsman_automation_ltd"
collections_to_test = ["pdf_text", "concalls", "images"]

q_chunk = generate_embeddings([{"content": "test query", "metadata": {}, "embedding": None}])
q_emb = q_chunk[0]["embedding"]

for c_type in collections_to_test:
    c_name = f"{company_slug}_{c_type}"
    # pdf path is "pdf" not "pdf_text" in chroma path
    folder_type = c_type
    if c_type == "pdf_text":
        folder_type = "pdf"
    if c_type == "concalls":
        folder_type = "concall"
    
    chroma_path = f"{settings.CHROMA_BASE_DIR}/{company_slug}/{folder_type}"
    
    print(f"\n--- Checking {c_name} ---")
    try:
        col = get_or_create_collection(c_name, chroma_path=chroma_path)
        count = col.count()
        print(f"collection.count() = {count}")
        
        if count > 0:
            results = query_collection(
                query_embedding=q_emb,
                collection_name=c_name,
                top_k=8,
                chroma_path=chroma_path
            )
            print(f"query_collection() returned {len(results)} chunks")
    except Exception as e:
        print(f"Error checking {c_name}: {e}")
