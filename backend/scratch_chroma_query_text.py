import chromadb

path = r"D:\FinBot\backend\chroma_store\craftsman_automation_ltd\excel"
client = chromadb.PersistentClient(path=path)
collection = client.get_collection("craftsman_automation_ltd_excel")

results = collection.query(
    query_texts=["What was the Net Profit reported by the company in FY26?"],
    n_results=8,
)
print("Query by text results:")
print(f"Number of documents: {len(results['documents'][0]) if results['documents'] else 0}")
