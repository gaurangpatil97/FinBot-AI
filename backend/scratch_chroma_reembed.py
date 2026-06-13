import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(r"D:\FinBot\backend"))

from app.core.ingestor import ingest_uploaded_file

company_slug = "craftsman_automation_ltd"
file_type = "excel"
file_path = Path(r"D:\FinBot\backend\data\uploads\craftsman_automation_ltd\excel\Craftsman Auto.xlsx")

print(f"Re-embedding {file_path} from scratch via ingest_uploaded_file...")
result = ingest_uploaded_file(
    company_slug=company_slug,
    file_type=file_type,
    file_path=file_path
)

print("Re-embedding complete!")
print(result)
