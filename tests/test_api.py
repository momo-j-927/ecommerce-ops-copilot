from fastapi.testclient import TestClient

from ecommerce_ops_agent.api import app


client = TestClient(app)


def test_health_endpoint() -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_query_endpoint_returns_structured_result() -> None:
    response = client.post("/query", json={"query": "扫描订单异常"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "anomaly_scan"
    assert payload["citations"]
