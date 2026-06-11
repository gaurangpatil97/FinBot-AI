"""
FinBot Retrieval Diagnostic Script — diagnose_retrieval.py
Retrieves top 20 chunks for failed PDF and Concall questions
and tells you whether the right chunk exists in the results.

Usage:
    cd D:\\FinBot
    python tests/questions/diagnose_retrieval.py

Output:
    tests/results/retrieval_diagnosis_TIMESTAMP.txt
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from pathlib import Path
from datetime import datetime
from app.core.embedder import generate_embeddings
from app.db.vector_store import query_collection
from config import settings

COMPANY_SLUG = "craftsman_automation_ltd"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_DIR = Path("tests/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RESULTS_DIR / f"retrieval_diagnosis_{TIMESTAMP}.txt"

# Failed questions to diagnose
# Format: (question, collection_type, year, what_we_expect_to_find)
FAILED_QUESTIONS = [
    # PDF failures
    (
        "According to the MD&A of the company for FY23, what was the stated reason for the decline in the Interest Coverage Ratio?",
        "pdf",
        "FY23",
        "interest coverage ratio decline reason increase interest cost"
    ),
    (
        "According to the MD&A of the company for FY24, what are the specific reasons cited for the deterioration in the Interest Coverage Ratio and the Debt-Equity Ratio?",
        "pdf",
        "FY24",
        "interest coverage ratio deterioration reason increase interest borrowings"
    ),
    (
        "According to the FY25 MD&A, what was management's stated explanation for the significant deterioration in ratios?",
        "pdf",
        "FY25",
        "one-time expenses acquisitions greenfield losses deterioration ratios"
    ),
    (
        "What were the two Key Audit Matters identified by the statutory auditors of the company for FY24?",
        "pdf",
        "FY24",
        "key audit matters derivative contracts PPE property plant equipment"
    ),
    (
        "The company's FY25 Directors Report states all RPTs were arm's length. However what does the BRSR data reveal about the concentration of loans and advances?",
        "pdf",
        "FY25",
        "BRSR loans advances related parties 0% 100%"
    ),
    (
        "The Statutory Auditors identified only one KAM in the standalone audit for FY25. What was it?",
        "pdf",
        "FY25",
        "key audit matter PPE property plant equipment standalone FY25"
    ),

    # Concall failures
    (
        "What was the total consolidated H1 FY23 revenue reported by the company?",
        "concall",
        None,
        "H1 FY23 revenue 1447 crores consolidated half year"
    ),
    (
        "What was the segment-wise EBIT for Auto Powertrain, Aluminum Products, and Industrial Engineering in FY23 Q1?",
        "concall",
        None,
        "Q1 FY23 EBIT segment powertrain aluminum industrial engineering 95 20 11"
    ),
    (
        "What was the total debt split between long-term and working capital loans as of FY22 Q4?",
        "concall",
        None,
        "debt FY22 Q4 long term working capital 522 193 713 crores"
    ),
    (
        "The company revised its full-year FY23 CAPEX guidance upward from 225 crores to 275 crores. What was the reason?",
        "concall",
        None,
        "CAPEX guidance revised 275 aluminium order additional capex"
    ),
]


def embed_query(question: str) -> list[float]:
    chunks = [{"content": question, "metadata": {}, "embedding": None}]
    embedded = generate_embeddings(chunks)
    return embedded[0]["embedding"]


def get_collection_path(collection_type: str) -> str:
    return f"{settings.CHROMA_BASE_DIR}/{COMPANY_SLUG}/{collection_type}"


def get_collection_name(collection_type: str) -> str:
    if collection_type == "pdf":
        return f"{COMPANY_SLUG}_pdf_text"
    elif collection_type == "concall":
        return f"{COMPANY_SLUG}_concalls"
    elif collection_type == "images":
        return f"{COMPANY_SLUG}_images"
    return f"{COMPANY_SLUG}_excel"


def diagnose_question(question, collection_type, year, expected_keywords):
    print(f"\n{'='*70}")
    print(f"Q: {question[:80]}...")
    print(f"Collection: {collection_type} | Year: {year}")
    print(f"Expected to find: {expected_keywords}")
    print(f"{'='*70}")

    embedding = embed_query(question)
    collection_name = get_collection_name(collection_type)
    chroma_path = get_collection_path(collection_type)

    # Retrieve top 20
    chunks = query_collection(
        query_embedding=embedding,
        collection_name=collection_name,
        top_k=20,
        year=year,
        chroma_path=chroma_path
    )

    if not chunks:
        print("  ❌ NO CHUNKS RETRIEVED — year filter may be too strict or collection empty")
        return {
            "question": question,
            "collection": collection_type,
            "year": year,
            "chunks_retrieved": 0,
            "right_chunk_found": False,
            "right_chunk_rank": None,
            "diagnosis": "NO_CHUNKS_RETRIEVED"
        }

    print(f"  Retrieved {len(chunks)} chunks")
    print()

    # Check if expected keywords appear in any chunk
    keywords = expected_keywords.lower().split()
    right_chunk_rank = None
    right_chunk_score = None

    for i, chunk in enumerate(chunks):
        content_lower = chunk["content"].lower()
        page = chunk["metadata"].get("page", chunk["metadata"].get("sheet", "?"))
        filename = chunk["metadata"].get("filename", "?")
        score = chunk["score"]

        # Count keyword matches
        matches = sum(1 for kw in keywords if kw in content_lower)
        match_pct = matches / len(keywords) * 100

        # Mark as right chunk if >40% keywords match
        is_right = match_pct >= 40

        marker = "✅" if is_right else "  "
        print(f"  {marker} Rank {i+1:2d} | Score: {score:.3f} | Page: {page} | File: {filename[-30:]}")
        print(f"         Keywords matched: {matches}/{len(keywords)} ({match_pct:.0f}%)")
        print(f"         Preview: {chunk['content'][:100].strip()}")
        print()

        if is_right and right_chunk_rank is None:
            right_chunk_rank = i + 1
            right_chunk_score = score

    # Diagnosis
    if right_chunk_rank is None:
        diagnosis = "CHUNK_NOT_IN_TOP_20 — may need reingestion or different chunking"
        print(f"  ❌ DIAGNOSIS: {diagnosis}")
    elif right_chunk_rank <= 3:
        diagnosis = "CHUNK_IN_TOP_3 — should be working, check generation"
        print(f"  ✅ DIAGNOSIS: {diagnosis} (rank {right_chunk_rank})")
    elif right_chunk_rank <= 8:
        diagnosis = "CHUNK_IN_TOP_8 — increase top_k or add reranker"
        print(f"  ⚠️  DIAGNOSIS: {diagnosis} (rank {right_chunk_rank})")
    else:
        diagnosis = "CHUNK_RANKED_LOW — reranker needed"
        print(f"  ⚠️  DIAGNOSIS: {diagnosis} (rank {right_chunk_rank})")

    return {
        "question": question,
        "collection": collection_type,
        "year": year,
        "chunks_retrieved": len(chunks),
        "right_chunk_found": right_chunk_rank is not None,
        "right_chunk_rank": right_chunk_rank,
        "right_chunk_score": right_chunk_score,
        "diagnosis": diagnosis
    }


def main():
    print(f"\n{'='*70}")
    print(f"  FinBot Retrieval Diagnostic")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Company: {COMPANY_SLUG}")
    print(f"  Questions to diagnose: {len(FAILED_QUESTIONS)}")
    print(f"{'='*70}")

    results = []
    for question, collection_type, year, expected in FAILED_QUESTIONS:
        result = diagnose_question(question, collection_type, year, expected)
        results.append(result)

    # Summary
    print(f"\n{'='*70}")
    print(f"  DIAGNOSTIC SUMMARY")
    print(f"{'='*70}")

    not_found = [r for r in results if not r["right_chunk_found"]]
    in_top3 = [r for r in results if r["right_chunk_found"] and r["right_chunk_rank"] <= 3]
    in_top8 = [r for r in results if r["right_chunk_found"] and 3 < r["right_chunk_rank"] <= 8]
    ranked_low = [r for r in results if r["right_chunk_found"] and r["right_chunk_rank"] > 8]

    print(f"\n  Chunk not in top 20:  {len(not_found)} — needs reingestion")
    print(f"  Chunk in top 3:       {len(in_top3)} — generation issue")
    print(f"  Chunk in top 8:       {len(in_top8)} — increase top_k")
    print(f"  Chunk ranked low:     {len(ranked_low)} — reranker needed")

    print(f"\n  RECOMMENDED FIX:")
    if len(not_found) > len(results) * 0.5:
        print(f"  → More than 50% chunks not found — chunking strategy needs review")
    elif len(ranked_low) + len(in_top8) > len(results) * 0.5:
        print(f"  → Most chunks exist but ranked low — ADD RERANKER")
    elif len(in_top3) > len(results) * 0.5:
        print(f"  → Chunks in top 3 but wrong answers — check generation/prompt")
    else:
        print(f"  → Mixed issues — increase top_k first, then add reranker")

    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"FinBot Retrieval Diagnostic\n")
        f.write(f"Run: {TIMESTAMP}\n")
        f.write(f"{'='*70}\n\n")
        for r in results:
            f.write(f"Q: {r['question'][:80]}\n")
            f.write(f"Collection: {r['collection']} | Year: {r['year']}\n")
            f.write(f"Chunks retrieved: {r['chunks_retrieved']}\n")
            f.write(f"Right chunk found: {r['right_chunk_found']}\n")
            f.write(f"Right chunk rank: {r['right_chunk_rank']}\n")
            f.write(f"Diagnosis: {r['diagnosis']}\n\n")

    print(f"\n  Results saved to: {OUTPUT_FILE}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()