import chromadb
from loguru import logger

path = r"D:\FinBot\backend\chroma_store\craftsman_automation_ltd\excel"
print(f"Connecting to ChromaDB at: {path}")

try:
    client = chromadb.PersistentClient(path=path)
    collections = client.list_collections()
    print(f"Found {len(collections)} collections:")
    for c in collections:
        count = c.count()
        print(f" - Collection '{c.name}' has {count} chunks")
except Exception as e:
    print(f"Failed to read ChromaDB: {e}")
