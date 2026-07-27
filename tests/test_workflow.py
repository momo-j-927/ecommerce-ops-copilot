from ecommerce_ops_agent.database import detect_order_anomalies, get_sales_summary
from ecommerce_ops_agent.workflow import classify_intent, run_query


def test_sales_summary_for_region() -> None:
    result = get_sales_summary("华南")
    assert result["order_count"] == 7
    assert result["revenue"] == 2984.0
    assert result["refund_rate_percent"] == 28.57


def test_anomaly_detection_returns_explainable_types() -> None:
    anomalies = detect_order_anomalies()
    assert len(anomalies) == 9
    assert {item["anomaly_type"] for item in anomalies} == {
        "zero_amount",
        "high_discount",
        "delivery_delay",
        "refund",
    }


def test_router_classifies_three_supported_intents() -> None:
    assert classify_intent("查询华南销售额")[0] == "sales_summary"
    assert classify_intent("扫描退款和高折扣异常")[0] == "anomaly_scan"
    assert classify_intent("促销审核规则是什么")[0] == "knowledge_query"


def test_unknown_request_requires_human_review() -> None:
    result = run_query("帮我看看这个")
    assert result.intent == "unclear"
    assert result.review_required is True
    assert "fallback:human_review" in result.trace


def test_knowledge_query_has_source_citation() -> None:
    result = run_query("退款流程应该如何处理")
    assert result.intent == "knowledge_query"
    assert result.citations
    assert any("refund_policy.md" in item for item in result.citations)


def test_workflow_records_tool_trace() -> None:
    result = run_query("华北订单量和客单价")
    assert result.intent == "sales_summary"
    assert any(item.startswith("tool:sales_summary") for item in result.trace)
