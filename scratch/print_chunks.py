import sys
sys.stdout.reconfigure(encoding='utf-8')
from app.core.rag import answer_query
from app.models.schemas import QueryRequest

q = "Astral's borrowings jumped from 119.40 in FY24 to 233.20 in FY25. Did operating cash flow cover the incremental debt? Compute the ratio of FY25 operating cash flow to the absolute increase in borrowings."
res = answer_query(QueryRequest(question=q, company_slug='astral_ltd'))

print('--- CHUNKS ---')
for i, c in enumerate(res.chunks):
    meta = c.get("metadata", {})
    source_type = meta.get("source_type", "unknown")
    sheet = meta.get("sheet", "unknown")
    year = meta.get("year", "unknown")
    print(f'Chunk {i+1} | Source: {source_type} | Sheet: {sheet} | Year: {year}')
    print(c.get('content', '')[:500])
    print('-'*40)
