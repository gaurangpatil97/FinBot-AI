import os
import sys

# Ensure backend is in path
sys.path.append(os.path.abspath(r"D:\FinBot\backend"))

from app.db.vector_store import query_collection


print("Generating embedding for question...")
question = "What was the Net Profit reported by the company in FY26?"
q_chunk = [{"content": question, "metadata": {}, "embedding": None}]
from app.core.embedder import generate_embeddings
q_chunk = generate_embeddings(q_chunk)
q_emb = q_chunk[0]["embedding"]

print("Querying collection...")
try:
    results = query_collection(
        query_embedding=q_emb,
        collection_name="craftsman_automation_ltd_excel",
        top_k=8
    )
    print(f"Retrieved chunks count: {len(results)}")
    if len(results) > 0:
        print(f"Sample score: {results[0]['score']}")
except Exception as e:
    print(f"Error querying: {e}")
