import json
from pathlib import Path

from ecommerce_ops_agent.workflow import run_query


ROOT = Path(__file__).resolve().parents[1]
cases = [
    json.loads(line)
    for line in (ROOT / "eval" / "eval_cases.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]

correct = 0
executed = 0
cited_or_reviewed = 0
for case in cases:
    result = run_query(case["query"])
    correct += result.intent == case["expected_intent"]
    executed += bool(result.trace and result.trace[-1] == "compose:done")
    cited_or_reviewed += bool(result.citations or result.review_required)

report = {
    "cases": len(cases),
    "intent_accuracy": round(correct / len(cases), 4),
    "workflow_completion_rate": round(executed / len(cases), 4),
    "citation_or_review_coverage": round(cited_or_reviewed / len(cases), 4),
}
print(json.dumps(report, ensure_ascii=False, indent=2))
