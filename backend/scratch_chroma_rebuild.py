import chromadb
import time

path = r"D:\FinBot\backend\chroma_store\craftsman_automation_ltd\excel"
client = chromadb.PersistentClient(path=path)
collection = client.get_collection("craftsman_automation_ltd_excel")

print(f"Collection count before get: {collection.count()}")

# Fetch everything including embeddings
results = collection.get(include=["embeddings", "documents", "metadatas"])

ids = results.get("ids", [])
documents = results.get("documents", [])
metadatas = results.get("metadatas", [])
embeddings = results.get("embeddings", [])

print(f"Retrieved {len(ids)} documents from SQLite.")

if len(ids) > 0 and len(embeddings) > 0:
    print("Deleting collection...")
    client.delete_collection("craftsman_automation_ltd_excel")
    time.sleep(1)
    
    print("Recreating collection...")
    new_collection = client.create_collection(
        name="craftsman_automation_ltd_excel",
        metadata={"hnsw:space": "cosine"}
    )
    
    print("Adding back to force HNSW rebuild...")
    new_collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )
    print("Add complete!")
else:
    print("No embeddings found or ids empty!")
    
# Small delay to let Chroma sync
time.sleep(2)
print(f"Collection count after rebuild: {client.get_collection('craftsman_automation_ltd_excel').count()}")
