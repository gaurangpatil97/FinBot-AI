import os
import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8')

ASTRAL_CONTENT = """Segment Reporting - Astral Ltd FY25 Annual Report, Page 208
Segment Reporting - Year ended March 31, 2025 vs March 31, 2024 (₹ in Million)

Segment Revenue:
Plumbing: FY25 = 41,963; FY24 = 41,420
Paints and Adhesives: FY25 = 16,361; FY24 = 14,994
Total Segment Revenue: FY25 = 58,324; FY24 = 56,414

Segment Profit:
Plumbing: FY25 = 6,126; FY24 = 6,054
Paints and Adhesives: FY25 = 1,150; FY24 = 1,396
Total Segment Profit: FY25 = 7,276; FY24 = 7,450

Reconciliation of Segment Profit to Consolidated Profit Before Tax (PBT):
Total Segment Profit: 7,276
Add: Unallocated Income/(Expenses) net: 178
Less: Finance costs: (291)
Less: Share of loss of joint venture: (1)
Consolidated Profit Before Tax (PBT): 7,336
(7,276 + 178 - 291 - 1 = 7,336)

Segment Assets as at March 31, 2025 (March 31, 2024):
Plumbing: 28,677 (24,623)
Paints and Adhesives: 15,603 (14,222)
Total Segment Assets: 44,280 (38,845)

Segment Liabilities as at March 31, 2025 (March 31, 2024):
Plumbing: 7,521 (7,657)
Paints and Adhesives: 3,432 (2,606)
Total Segment Liabilities: 10,953 (10,263)"""

CRAFTSMAN_CONTENT = """Ratio Analysis - Craftsman Automation FY22 Annual Report, Page 93
Ratio Analysis - FY 21-22 vs FY 20-21

(a) Current Ratio: FY22 = 1.03; FY21 = 0.96; % Variance = 7%
(b) Debt-Equity Ratio: FY22 = 0.63; FY21 = 0.72; % Variance = -13%
(c) Debt Service Coverage Ratio: FY22 = 1.70; FY21 = 1.32; % Variance = 28%
(d) Return on Equity Ratio: FY22 = 15%; FY21 = 11%; % Variance = 34%
(e) Inventory Turnover Ratio: FY22 = 4.33; FY21 = 4.34; % Variance = 0%
(f) Trade Receivables Turnover Ratio: FY22 = 8.33; FY21 = 7.21; % Variance = 16%
Interest Coverage Ratio: FY22 = 6.40x; FY21 = 4.17x; % Variance = +53%
(Management attributes the Interest Coverage Ratio change to reduction
in interest cost from ₹107 Cr to ₹84 Cr and increase in EBITDA from
₹447 Cr to ₹539 Cr)"""

TARGETS = [
    {
        "company": "astral_ltd",
        "filename": "Astral_Ltd_AR_FY2025_AnnualReport.pdf",
        "page": 208,
        "content": ASTRAL_CONTENT,
        "source": "D:\\FinBot\\backend\\data\\uploads\\astral_ltd\\pdf\\Astral_Ltd_AR_FY2025_AnnualReport.pdf"
    },
    {
        "company": "craftsman_automation_ltd",
        "filename": "7.-Annual-Report-2021-22.pdf",
        "page": 93,
        "content": CRAFTSMAN_CONTENT,
        "source": "D:\\FinBot\\backend\\data\\uploads\\craftsman_automation_ltd\\pdf\\7.-Annual-Report-2021-22.pdf"
    }
]

CHROMA_STORE = "D:/FinBot/backend/chroma_store"

def process_manual_tables(dry_run=True):
    new_chunks = []
    
    for t in TARGETS:
        company = t["company"]
        filename = t["filename"]
        page = t["page"]
        content = t["content"]
        source_path = t["source"]
        
        chunk = {
            "content": content,
            "metadata": {
                "filename": filename,
                "page": page,
                "source": source_path,
                "chunk_type": "manual_table",
                "chunk_index": 0
            }
        }
        new_chunks.append((company, chunk))
        
    if not dry_run:
        # Actual embedding and insertion
        sys.path.append("D:/FinBot/backend")
        from app.core.embedder import generate_embeddings
        from app.db.vector_store import store_chunks
        
        chunks_by_company = {}
        for comp, chunk in new_chunks:
            if comp not in chunks_by_company:
                chunks_by_company[comp] = []
            chunks_by_company[comp].append(chunk)
            
        for comp, chunks in chunks_by_company.items():
            print(f"\nEmbedding {len(chunks)} manual chunks for {comp}...")
            embedded_chunks = generate_embeddings(chunks)
            collection_name = f"{comp}_pdf_text"
            
            db_path = os.path.join(CHROMA_STORE, comp, "pdf")
            print(f"Inserting into {collection_name} at {db_path}...")
            store_chunks(embedded_chunks, collection_name, chroma_path=db_path)
            
        print("\n=== ACTUAL INSERTION COMPLETE ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--insert", action="store_true", help="Run actual insertion")
    args = parser.parse_args()
    
    dry_run = not args.insert
    process_manual_tables(dry_run=dry_run)
