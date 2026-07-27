from fastapi import FastAPI

from .models import QueryRequest, QueryResponse
from .workflow import run_query


app = FastAPI(
    title="Ecommerce Ops Copilot",
    description="电商指标、异常与运营知识协同 Agent",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return run_query(request.query)
