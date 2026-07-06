import sys
import os
import json

# Add backend to path
sys.path.append(os.path.abspath('backend'))

from app.models.schemas import QueryRequest
from app.core.rag import answer_query
from loguru import logger

# Add a specific log handler so we can see the output
logger.add(sys.stdout, format="{message}", level="DEBUG")

question = "What are the key revenue drivers and priorities outlined by management for the coming year?"
company_slug = "craftsman_automation_ltd"

print("\n--- RUNNING QUERY ---")
req = QueryRequest(question=question, company_slug=company_slug)
try:
    res = answer_query(req)
    print("\n--- RESULT ---")
    print("Actual Answer Preview:", res.answer[:100] + "...")
    print("Citations:")
    for c in res.citations:
        print(f"  - {c.filename} Page {c.page}")
except Exception as e:
    print("Error:", e)
