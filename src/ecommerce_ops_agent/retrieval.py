import math
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge"


def tokenize(text: str) -> list[str]:
    compact = "".join(re.findall(r"[\u4e00-\u9fff]", text))
    chinese = list(compact)
    chinese += [compact[index : index + 2] for index in range(max(0, len(compact) - 1))]
    latin = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return chinese + latin


def search_knowledge(query: str, top_k: int = 2) -> list[dict[str, str | float]]:
    documents = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        documents.append((path.name, content, Counter(tokenize(content))))
    query_terms = Counter(tokenize(query))
    total = len(documents)
    document_frequency = Counter()
    for term in query_terms:
        document_frequency[term] = sum(1 for _, _, counts in documents if term in counts)
    results = []
    for source, content, counts in documents:
        score = 0.0
        for term, query_count in query_terms.items():
            if counts[term]:
                inverse_document_frequency = math.log(
                    (total + 1) / (document_frequency[term] + 1)
                ) + 1
                score += query_count * (1 + math.log(counts[term])) * inverse_document_frequency
        if score > 0:
            results.append(
                {
                    "source": source,
                    "score": round(score, 4),
                    "content": content.replace("\n", " ").strip(),
                }
            )
    return sorted(results, key=lambda item: float(item["score"]), reverse=True)[:top_k]
