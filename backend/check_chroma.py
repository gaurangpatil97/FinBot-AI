import chromadb

try:
    client = chromadb.PersistentClient(path=r'D:\FinBot\backend\chroma_store\craftsman_automation_ltd\pdf_text')
    collection = client.get_collection('craftsman_automation_ltd_pdf_text')
    print('Total chunks in collection:', collection.count())
    results = collection.get(limit=5, include=['metadatas'])
    for meta in results.get('metadatas', []):
        print(meta)
except Exception as e:
    print("Error:", e)
