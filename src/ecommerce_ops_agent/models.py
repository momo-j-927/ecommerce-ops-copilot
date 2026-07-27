from typing import Any, Literal

from pydantic import BaseModel, Field


Intent = Literal["sales_summary", "anomaly_scan", "knowledge_query", "unclear"]


class QueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)


class QueryResponse(BaseModel):
    query: str
    intent: Intent
    confidence: float
    answer: str
    data: dict[str, Any] | list[dict[str, Any]] | None = None
    citations: list[str] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)
    review_required: bool = False
