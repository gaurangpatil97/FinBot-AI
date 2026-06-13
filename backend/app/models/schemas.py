from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    company_slug: str
    year: Optional[str] = None
    session_id: Optional[str] = None
    use_history: bool = False


class Citation(BaseModel):
    filename: str
    page: Optional[Any] = None
    collection: str


class ChartSeries(BaseModel):
    name: str
    data: List[float]


class ChartData(BaseModel):
    chart_type: str  # "bar" | "line" | "combo"
    title: str
    x_axis: List[str]
    series: List[ChartSeries]
    y_axis_label: Optional[str] = None


class ChartRequest(BaseModel):
    company_slug: str
    metrics: List[str]
    years: Optional[List[str]] = None
    chart_type_hint: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    collections_searched: List[str] = Field(default_factory=list)
    agent_used: str
    agent_trace: str = ""
    chunks: list[dict] = []  # Retrieved chunks — populated during eval mode for RAGAS
    routing_debug: Dict[str, Any] = Field(default_factory=dict)
    chart_data: Optional[ChartData] = None


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    company_slug: str
    file_type: str
    status: str


class EmbedRequest(BaseModel):
    company_slug: str
    file_type: str


class EmbedResponse(BaseModel):
    status: str
    chunks_created: int
    collection_name: str


class CompanyCollectionStatus(BaseModel):
    status: str
    chunks: int = 0


class CompanyStatus(BaseModel):
    name: str
    slug: str
    ticker: str
    collections: Dict[str, CompanyCollectionStatus]
    files: List[Dict[str, Any]] = Field(default_factory=list)


class CompanyCreateRequest(BaseModel):
    name: str
    slug: str
    ticker: str


class CompanyRecord(BaseModel):
    name: str
    slug: str
    ticker: str
    collections: Dict[str, CompanyCollectionStatus] = Field(default_factory=dict)
    files: List[Dict[str, Any]] = Field(default_factory=list)
