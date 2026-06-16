import sys
from pathlib import Path
sys.path.append(r'D:\FinBot\backend')
from app.db.vector_store import get_persistent_client
from config import settings

company_slug = 'craftsman_automation_ltd'
collection_name = f'{company_slug}_pdf_text'

# In rag.py, it constructs the path like so:
path = f"{settings.CHROMA_BASE_DIR}/{company_slug}/pdf"
print(f"Checking Path: {path}")

client = get_persistent_client(path)
print("Collections available:", [c.name for c in client.list_collections()])

try:
    collection = client.get_collection(collection_name)
    print(f"\n--- Collection {collection_name} ---")
    print('Total chunks:', collection.count())
    results = collection.get(limit=5, include=['metadatas'])
    for meta in results.get('metadatas', []):
        print(meta)
except Exception as e:
    print('Error getting collection:', e)

print("\n--------------------------\n")
# Also let's check the pdf_text folder just in case
path2 = f"{settings.CHROMA_BASE_DIR}/{company_slug}/pdf_text"
print(f"Checking Path: {path2}")
try:
    client2 = get_persistent_client(path2)
    print("Collections available:", [c.name for c in client2.list_collections()])
    collection2 = client2.get_collection(collection_name)
    print(f"\n--- Collection {collection_name} ---")
    print('Total chunks:', collection2.count())
    results2 = collection2.get(limit=5, include=['metadatas'])
    for meta in results2.get('metadatas', []):
        print(meta)
except Exception as e:
    print('Error getting collection:', e)

