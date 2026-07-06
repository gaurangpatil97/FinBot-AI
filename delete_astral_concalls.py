import os
import sys
from pathlib import Path
import chromadb

def main():
    # Path to ChromaDB for astral_ltd concalls
    chroma_path = os.path.abspath(r"D:\FinBot\backend\chroma_store\astral_ltd\concall")
    collection_name = "astral_ltd_concalls"
    
    print(f"Connecting to ChromaDB at: {chroma_path}")
    
    try:
        client = chromadb.PersistentClient(path=chroma_path)
        
        # Check available collections
        collections = [c.name for c in client.list_collections()]
        print(f"Available collections in this path: {collections}")
        
        if collection_name not in collections:
            print(f"Collection '{collection_name}' not found in this database instance.")
            return
            
        collection = client.get_collection(collection_name)
        count_before = collection.count()
        print(f"Current count of chunks in '{collection_name}' before deletion: {count_before}")
        
        if count_before > 0:
            print("Deleting and recreating the collection to guarantee all documents are cleared...")
            client.delete_collection(name=collection_name)
            
            # Recreate the collection with cosine distance metric as configured in backend code
            collection = client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"Collection '{collection_name}' has been successfully recreated.")
        else:
            print("Collection is already empty.")
            
        count_after = collection.count()
        print(f"Count after deletion/recreation: {count_after}")
        
        if count_after == 0:
            print("Verification successful: count is exactly 0.")
        else:
            print("Verification failed: count is not 0.")
            
    except Exception as e:
        print(f"Error executing ChromaDB operations: {e}")

if __name__ == "__main__":
    main()
