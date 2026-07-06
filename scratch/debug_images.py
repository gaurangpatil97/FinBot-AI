import chromadb
from chromadb.config import Settings as ChromaSettings
import sys
sys.path.insert(0, '/app')
from app.core.embedder import generate_embeddings

# Simulate the exact code path used by the server
path = '/app/chroma_store/craftsman_automation_ltd/images'
client = chromadb.PersistentClient(path=path, settings=ChromaSettings(anonymized_telemetry=False))
coll = client.get_or_create_collection(name='craftsman_automation_ltd_images', metadata={"hnsw:space": "cosine"})

print(f"Collection count: {coll.count()}")

# Generate a real embedding for a test query
test_q = "revenue split by business segment donut chart FY22"
chunks = [{"content": test_q, "metadata": {}, "embedding": None}]
embedded = generate_embeddings(chunks)
query_emb = embedded[0]["embedding"]
print(f"Embedding dim: {len(query_emb)}")

# Query exactly like the server does
where = {"$and": [{"chunk_type": "image"}, {"year": "FY22"}]}
results = coll.query(
    query_embeddings=[query_emb],
    n_results=3,
    where=where,
    include=["documents", "metadatas", "distances"]
)
print(f"Results count: {len(results['documents'][0])}")
for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
    print(f"  - Page {meta.get('page')}: {doc[:80]}...")
