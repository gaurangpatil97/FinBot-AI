import chromadb
import sys

sys.stdout.reconfigure(encoding='utf-8')

def check_collection(db_path, collection_name, queries):
    print(f"\n=========================================")
    print(f"Checking Collection: {collection_name} in {db_path}")
    print(f"=========================================\n")
    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection(collection_name)
    except Exception as e:
        print(f"Collection {collection_name} not found: {e}")
        return
        
    for q in queries:
        print(f"--- Querying for: '{q}' ---")
        results = collection.get(
            where_document={"$contains": q},
            limit=3
        )
        if not results['documents']:
            print("No results found.\n")
            continue
            
        for i, doc in enumerate(results['documents']):
            meta = results['metadatas'][i]
            print(f"Result {i+1}: Page {meta.get('page')}")
            snippet = doc[:300].replace('\n', ' ')
            print(f"Content: {snippet}...\n")
            
check_collection("D:/FinBot/backend/chroma_store/astral_ltd/pdf", "astral_ltd_pdf_text", ["Contingent Liabilities", "Other Expenses"])
check_collection("D:/FinBot/backend/chroma_store/craftsman_automation_ltd/pdf", "craftsman_automation_ltd_pdf_text", ["Contingent Liabilities", "Other Expenses"])
