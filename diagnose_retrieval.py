import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = str(Path(__file__).resolve().parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.embedder import generate_embeddings
from app.db.vector_store import query_collection
from config import settings

COMPANY_SLUG = "astral_ltd"

# Question map with (id, text, collection_type, chroma_path, collection_name)
TARGET_QUESTIONS = [
    {
        "id": "Q29",
        "text": "What was the installed capacity of Astral Ltd for the year under review as mentioned in the Project Implementation section of the Directors' Report, and by what percentage did it increase compared to the previous year?",
        "type": "pdf",
        "chroma_path": f"{settings.CHROMA_BASE_DIR}/{COMPANY_SLUG}/pdf",
        "collection_name": f"{COMPANY_SLUG}_pdf_text"
    },
    {
        "id": "Q31",
        "text": "In Note 37 (Segment Reporting), the Group reports segment revenues and profits for 'Plastic' and 'Adhesives'. Show how the total segment profit reconciles to the Consolidated Profit Before Tax of ₹6,485 million stated in the Financial Highlights of the Directors' Report, detailing each unallocable item and its amount.",
        "type": "pdf",
        "chroma_path": f"{settings.CHROMA_BASE_DIR}/{COMPANY_SLUG}/pdf",
        "collection_name": f"{COMPANY_SLUG}_pdf_text"
    },
    {
        "id": "Q49",
        "text": "Review the evolution of cost-control commentary and absolute branding outlays between Q1 FY25 and Q2 FY25.",
        "type": "concall",
        "chroma_path": f"{settings.CHROMA_BASE_DIR}/{COMPANY_SLUG}/concall",
        "collection_name": f"{COMPANY_SLUG}_concalls"
    },
    {
        "id": "Q58",
        "text": "What is the trajectory of Astral's reported production capacity in India (in Metric Tonnes) across the visual infrastructure metrics from FY22 to FY25?",
        "type": "images",
        "chroma_path": f"{settings.CHROMA_BASE_DIR}/{COMPANY_SLUG}/images",
        "collection_name": f"{COMPANY_SLUG}_images"
    }
]

def main():
    print("=== FinBot Retrieval Diagnostics ===")
    print(f"Production TOP_K_CHUNKS: {settings.TOP_K_CHUNKS}")
    print(f"Production TOP_K_PDF: {settings.TOP_K_PDF}")
    print(f"Production TOP_K_CONCALL: {settings.TOP_K_CONCALL}")
    print(f"Production TOP_K_MULTI: {settings.TOP_K_CHUNKS_MULTI}")
    print("====================================")

    output_lines = []
    output_lines.append("# Retrieval Diagnostics Report - Astral")
    output_lines.append("")
    output_lines.append("## Production Baseline Settings")
    output_lines.append(f"- **TOP_K_CHUNKS**: {settings.TOP_K_CHUNKS}")
    output_lines.append(f"- **TOP_K_PDF**: {settings.TOP_K_PDF}")
    output_lines.append(f"- **TOP_K_CONCALL**: {settings.TOP_K_CONCALL}")
    output_lines.append(f"- **TOP_K_CHUNKS_MULTI**: {settings.TOP_K_CHUNKS_MULTI}")
    output_lines.append("")

    for q in TARGET_QUESTIONS:
        q_id = q["id"]
        q_text = q["text"]
        source_type = q["type"]
        chroma_path = q["chroma_path"]
        collection_name = q["collection_name"]

        print(f"Retrieving for {q_id} ({source_type})...")
        
        # Generate query embedding
        query_chunks = [{"content": q_text, "metadata": {}, "embedding": None}]
        query_embedding = generate_embeddings(query_chunks)[0]["embedding"]

        # Run retrieval with k=20
        if source_type == "images":
            from app.db.vector_store import query_collection_by_type
            retrieved_chunks = query_collection_by_type(
                query_embedding,
                collection_name,
                chunk_type="image",
                year=None,
                top_k=20,
                chroma_path=chroma_path
            )
        else:
            retrieved_chunks = query_collection(
                query_embedding,
                collection_name,
                top_k=20,
                year=None,
                chroma_path=chroma_path
            )

        output_lines.append(f"## {q_id}: {q_text}")
        output_lines.append(f"- **Source Type**: {source_type}")
        output_lines.append(f"- **Collection Name**: {collection_name}")
        output_lines.append(f"- **Chroma Path**: {chroma_path}")
        output_lines.append("")
        output_lines.append("| Rank | Score | Source Document | Chunk Snippet |")
        output_lines.append("|---|---|---|---|")

        for rank, chunk in enumerate(retrieved_chunks, 1):
            score = chunk["score"]
            meta = chunk["metadata"]
            filename = meta.get("filename", "unknown")
            page = meta.get("page", "")
            page_str = f" (Page {page})" if page else ""
            source_doc = f"{filename}{page_str}"
            
            # Clean up content snippet for table display
            content = chunk["content"].replace("\n", " ").replace("|", "\\|")
            if len(content) > 150:
                content_snippet = content[:150] + "..."
            else:
                content_snippet = content
                
            output_lines.append(f"| {rank} | {score:.4f} | {source_doc} | {content_snippet} |")
        
        output_lines.append("")
        output_lines.append("### Full retrieved chunks details:")
        output_lines.append("")
        for rank, chunk in enumerate(retrieved_chunks, 1):
            score = chunk["score"]
            meta = chunk["metadata"]
            filename = meta.get("filename", "unknown")
            page = meta.get("page", "")
            page_str = f" (Page {page})" if page else ""
            source_doc = f"{filename}{page_str}"
            output_lines.append(f"#### Rank {rank} | Score: {score:.4f} | Source: {source_doc}")
            output_lines.append("```text")
            output_lines.append(chunk["content"])
            output_lines.append("```")
            output_lines.append("")
        output_lines.append("---")
        output_lines.append("")

    with open("d:/FinBot/retrieval_diagnosis_astral.md", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print("\nSuccessfully generated retrieval_diagnosis.md!")

if __name__ == "__main__":
    main()
