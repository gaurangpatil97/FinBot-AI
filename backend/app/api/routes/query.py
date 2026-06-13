from __future__ import annotations

from fastapi import APIRouter

from app.core.rag import answer_query
from app.models.schemas import QueryRequest, QueryResponse

router = APIRouter(tags=["query"])


import time
from app.db import sessions_db

@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    start_time = time.time()
    response = answer_query(request)
    latency = time.time() - start_time
    
    if request.session_id:
        # Save user message
        sessions_db.add_message(
            session_id=request.session_id,
            role="user",
            content=request.question,
            citations=[],
            routing_debug={},
            latency=0.0
        )
        
        # Save assistant message
        sessions_db.add_message(
            session_id=request.session_id,
            role="assistant",
            content=response.answer,
            citations=response.citations,
            routing_debug=response.routing_debug,
            latency=latency
        )
        
    return response
