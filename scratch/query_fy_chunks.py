import json
import chromadb

def main():
    client = chromadb.PersistentClient(path='/app/chroma_store/craftsman_automation_ltd/images')
    coll = client.get_or_create_collection('craftsman_automation_ltd_images')
    print('Total count:', coll.count())
    # Query for years FY18-FY21
    results = coll.get(include=['metadatas'], where={'year': {'$in': ['FY18','FY19','FY20','FY21']}})
    print('FY18-21 chunks found:', len(results['metadatas']))
    for m in results['metadatas']:
        print(m)

if __name__ == "__main__":
    main()
