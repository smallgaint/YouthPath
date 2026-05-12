from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.documents import Document

from core.rag import index_documents


def load_policy_files(data_dir: str = "data/policies") -> list[dict[str, Any]]:
    policies = []
    for path in sorted(Path(data_dir).glob("*.json")):
        policies.append(json.loads(path.read_text(encoding="utf-8")))
    return policies


def build_documents(policies: list[dict[str, Any]], chunk_size: int = 1000, overlap: int = 100) -> list[Document]:
    documents: list[Document] = []
    for policy in policies:
        text = _policy_text(policy)
        if not text:
            continue
        chunks = _chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        for idx, chunk in enumerate(chunks):
            policy_id = str(policy.get("policy_id") or policy.get("title") or "")
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "chunk_id": f"{policy_id}:{idx}",
                        "policy_id": policy_id,
                        "title": str(policy.get("title") or ""),
                        "region": str(policy.get("region") or ""),
                        "min_age": policy.get("min_age") if policy.get("min_age") is not None else -1,
                        "max_age": policy.get("max_age") if policy.get("max_age") is not None else -1,
                        "deadline": str(policy.get("deadline") or ""),
                        "category": str(policy.get("category") or ""),
                    },
                )
            )
    return documents


def _policy_text(policy: dict[str, Any]) -> str:
    parts = [
        f"정책명: {policy.get('title') or ''}",
        f"분야: {policy.get('category') or ''}",
        f"지역: {policy.get('region') or ''}",
        f"나이: {policy.get('min_age') or ''}~{policy.get('max_age') or ''}",
        f"소득: {policy.get('income') or ''}",
        f"신청기간: {policy.get('deadline') or ''}",
        f"설명: {policy.get('description') or ''}",
        f"상세: {policy.get('detail') or ''}",
    ]
    return "\n".join(part for part in parts if part.strip())


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/policies")
    parser.add_argument("--collection", default="policies")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=100)
    args = parser.parse_args()

    policies = load_policy_files(args.data_dir)
    docs = build_documents(policies, chunk_size=args.chunk_size, overlap=args.overlap)
    index_documents(args.collection, docs)
    print(json.dumps({"policies": len(policies), "chunks": len(docs)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
