from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from .database import detect_order_anomalies, get_sales_summary
from .models import Intent, QueryResponse
from .retrieval import search_knowledge


class AgentState(TypedDict, total=False):
    query: str
    intent: Intent
    confidence: float
    data: dict[str, Any] | list[dict[str, Any]] | None
    citations: list[str]
    answer: str
    trace: list[str]
    review_required: bool


REGIONS = ("华南", "华东", "华北", "西南")


def classify_intent(query: str) -> tuple[Intent, float]:
    keyword_groups: list[tuple[Intent, tuple[str, ...]]] = [
        ("anomaly_scan", ("异常", "核验", "退款", "延迟", "折扣", "风险", "高金额")),
        ("sales_summary", ("销售额", "营收", "订单量", "客单价", "退款率", "指标")),
        ("knowledge_query", ("规则", "制度", "流程", "sop", "怎么办", "如何处理", "审核")),
    ]
    normalized = query.lower()
    scores = {
        intent: sum(1 for keyword in keywords if keyword in normalized)
        for intent, keywords in keyword_groups
    }
    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]
    if best_score == 0:
        return "unclear", 0.25
    if sum(score == best_score for score in scores.values()) > 1:
        return "unclear", 0.45
    return best_intent, min(0.95, 0.65 + 0.1 * best_score)


def route_request(state: AgentState) -> AgentState:
    intent, confidence = classify_intent(state["query"])
    return {
        "intent": intent,
        "confidence": confidence,
        "trace": [*state.get("trace", []), f"route:{intent}:{confidence:.2f}"],
        "review_required": confidence < 0.6,
    }


def run_sales_tool(state: AgentState) -> AgentState:
    region = next((item for item in REGIONS if item in state["query"]), None)
    data = get_sales_summary(region)
    return {
        "data": data,
        "citations": ["data/orders.csv"],
        "trace": [*state["trace"], f"tool:sales_summary:region={region or 'all'}"],
    }


def run_anomaly_tool(state: AgentState) -> AgentState:
    data = detect_order_anomalies()
    return {
        "data": data,
        "citations": ["data/orders.csv", "data/knowledge/order_anomaly_sop.md"],
        "trace": [*state["trace"], f"tool:anomaly_scan:count={len(data)}"],
    }


def run_knowledge_tool(state: AgentState) -> AgentState:
    data = search_knowledge(state["query"])
    citations = [f"data/knowledge/{item['source']}" for item in data]
    return {
        "data": data,
        "citations": citations,
        "review_required": not data,
        "trace": [*state["trace"], f"tool:knowledge_query:hits={len(data)}"],
    }


def mark_for_review(state: AgentState) -> AgentState:
    return {
        "data": None,
        "citations": [],
        "review_required": True,
        "trace": [*state["trace"], "fallback:human_review"],
    }


def count_types(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = str(item["anomaly_type"])
        counts[key] = counts.get(key, 0) + 1
    return counts


def compose_answer(state: AgentState) -> AgentState:
    intent = state["intent"]
    if intent == "sales_summary":
        data = state["data"]
        answer = (
            f"{data['region']}共有 {data['order_count']} 笔订单，营收 {data['revenue']:.2f} 元，"
            f"客单价 {data['average_order_value']:.2f} 元，退款率 "
            f"{data['refund_rate_percent']:.2f}%。"
        )
    elif intent == "anomaly_scan":
        data = state["data"]
        summary = "、".join(
            f"{key} {value} 笔" for key, value in count_types(data).items()
        )
        answer = (
            f"共识别 {len(data)} 笔待核验订单：{summary}。"
            "建议按异常核验 SOP 交由业务人员复核。"
        )
    elif intent == "knowledge_query":
        data = state["data"]
        answer = (
            "检索到的运营规则：" + " ".join(item["content"] for item in data)
            if data
            else "现有知识库没有足够依据，已标记为需要人工补充或复核。"
        )
    else:
        answer = "当前请求无法可靠归类。请补充要查询的指标、异常类型或业务规则。"
    return {"answer": answer, "trace": [*state["trace"], "compose:done"]}


builder = StateGraph(AgentState)
builder.add_node("route", route_request)
builder.add_node("sales", run_sales_tool)
builder.add_node("anomaly", run_anomaly_tool)
builder.add_node("knowledge", run_knowledge_tool)
builder.add_node("review", mark_for_review)
builder.add_node("compose", compose_answer)
builder.set_entry_point("route")
builder.add_conditional_edges(
    "route",
    lambda state: state["intent"],
    {
        "sales_summary": "sales",
        "anomaly_scan": "anomaly",
        "knowledge_query": "knowledge",
        "unclear": "review",
    },
)
for node in ("sales", "anomaly", "knowledge", "review"):
    builder.add_edge(node, "compose")
builder.add_edge("compose", END)
graph = builder.compile()


def run_query(query: str) -> QueryResponse:
    result = graph.invoke({"query": query, "trace": []})
    return QueryResponse(
        query=query,
        intent=result["intent"],
        confidence=result["confidence"],
        answer=result["answer"],
        data=result.get("data"),
        citations=result.get("citations", []),
        trace=result["trace"],
        review_required=result.get("review_required", False),
    )
