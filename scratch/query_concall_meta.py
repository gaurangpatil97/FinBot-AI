import sys
from pathlib import Path

# Add backend to path so we can import from app
sys.path.append(r"d:\FinBot\backend")

from app.db.vector_store import get_persistent_client
from app.core.rag import normalize_pdf_year
from config import settings

# ChromaDB for craftsman concalls
chroma_path = f"{settings.CHROMA_BASE_DIR}/craftsman_automation_ltd/concall"
client = get_persistent_client(chroma_path)
collection = client.get_collection("craftsman_automation_ltd_concalls")

# Fetch a few chunks
results = collection.get(limit=5, include=["metadatas"])
metadatas = results.get("metadatas", [])

print("--- RAW METADATA ---")
for meta in metadatas:
    print(f"Filename: {meta.get('filename')} | Year: {meta.get('year')} | Quarter: {meta.get('quarter')}")

print("\n--- NORMALIZE_PDF_YEAR() OUTPUT ---")
test_years = ["FY25", "2025", "25", "FY 2025"]
for y in test_years:
    print(f"Input: {y} -> Output: {normalize_pdf_year(y)}")
