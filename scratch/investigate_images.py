import chromadb
from collections import Counter

for company in ['astral_ltd', 'craftsman_automation_ltd']:
    client = chromadb.PersistentClient(path=f'/app/chroma_store/{company}/images')
    coll = client.get_or_create_collection(f'{company}_images')
    
    results = coll.get(include=['metadatas'], limit=15)
    print(f'\n======================================================')
    print(f'=== {company} Sample Metadata ===')
    print(f'======================================================')
    for m in results['metadatas']:
        print(m)
        
    all_results = coll.get(include=['metadatas'])
    all_metadatas = all_results['metadatas']
    
    total_chunks = len(all_metadatas)
    years = [m.get('year') for m in all_metadatas if m is not None]
    
    year_counts = Counter(years)
    print(f'\n=== {company} Year Distribution ===')
    print(f'Total chunks: {total_chunks}')
    
    missing_year = sum(1 for y in years if y is None)
    print(f'Missing/Null year field: {missing_year}')
    
    print('Distribution:')
    for y, count in sorted(year_counts.items(), key=lambda x: str(x[0])):
        print(f'  {y}: {count}')

print("\n\n=== normalize_pdf_year Test ===")
import sys
sys.path.insert(0, '/app')
from app.core.rag import normalize_pdf_year

test_years = [None, "FY22", "FY2022", "2022", "2023", "23", "FY23"]
for y in test_years:
    print(f"normalize_pdf_year({repr(y)}) -> {repr(normalize_pdf_year(y))}")
