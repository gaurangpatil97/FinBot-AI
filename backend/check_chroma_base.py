import sys
sys.path.append(r'D:\FinBot\backend')
from app.db.vector_store import get_persistent_client
from config import settings

path = settings.CHROMA_BASE_DIR
print(f"Using CHROMA_BASE_DIR: {path}")

client = get_persistent_client(path)
print("Collections available:", [c.name for c in client.list_collections()])

try:
    collection = client.get_collection('craftsman_automation_ltd_pdf_text')
    print('Total chunks in collection:', collection.count())
    results = collection.get(limit=5, include=['metadatas'])
    for meta in results.get('metadatas', []):
        print(meta)
except Exception as e:
    print('Error:', e)
