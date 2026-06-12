import chromadb

path = r"D:\FinBot\backend\chroma_store\craftsman_automation_ltd\excel"
client = chromadb.PersistentClient(path=path)
collection = client.get_collection("craftsman_automation_ltd_excel")

results = collection.get()
print(f"Number of documents in get(): {len(results['documents'])}")
if len(results['documents']) > 0:
    print(f"Sample metadata: {results['metadatas'][0]}")
