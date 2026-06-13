from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.db import sessions_db

router = APIRouter(prefix="/sessions", tags=["sessions"])

class CreateSessionRequest(BaseModel):
    company_slug: str
    title: Optional[str] = None

class RenameSessionRequest(BaseModel):
    title: str

@router.post("")
def create_session(req: CreateSessionRequest):
    return sessions_db.create_session(req.company_slug, req.title)

@router.get("")
def list_sessions(company_slug: str = Query(...)):
    return sessions_db.list_sessions(company_slug)

@router.get("/{session_id}/messages")
def get_messages(session_id: str):
    session = sessions_db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions_db.get_messages(session_id)

@router.patch("/{session_id}")
def rename_session(session_id: str, req: RenameSessionRequest):
    success = sessions_db.rename_session(session_id, req.title)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success"}

@router.delete("/{session_id}")
def delete_session(session_id: str):
    success = sessions_db.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success"}
