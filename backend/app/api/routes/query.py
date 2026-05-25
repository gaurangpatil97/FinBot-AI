from __future__ import annotations

from fastapi import APIRouter

from app.core.rag import answer_query
from app.models.schemas import QueryRequest, QueryResponse

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return answer_query(request)
