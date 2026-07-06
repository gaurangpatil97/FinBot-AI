import json
import chromadb

def main():
    client = chromadb.PersistentClient(path='/app/chroma_store/craftsman_automation_ltd/images')
    coll = client.get_or_create_collection('craftsman_automation_ltd_images')
    print('Total count:', coll.count())
    filenames = ['7.-Annual-Report-2021-22.pdf', 'Annual-Report_2023.pdf', 'Annual-Report-2023-24.pdf']
    for fn in filenames:
        results = coll.get(include=['metadatas'], where={'filename': fn})
        print(f'Filename {fn} chunks:', len(results['metadatas']))
        for m in results['metadatas']:
            print(m)

if __name__ == "__main__":
    main()
