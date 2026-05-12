from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clients.ontong_api import fetch_policies, normalize_policy, save_policy_json


DEFAULT_QUERIES = [
    "청년 주거",
    "청년 취업",
    "청년 복지",
    "청년 교육",
    "청년 창업",
]


def collect(
    max_items: int = 60,
    display: int = 10,
    output_dir: str = "data/policies",
    queries: list[str] | None = None,
    per_query: int | None = None,
) -> list[Path]:
    saved: list[Path] = []
    seen: set[str] = set()

    for query in queries or DEFAULT_QUERIES:
        query_saved = 0
        page = 1
        while len(saved) < max_items:
            response = fetch_policies(query=query, page=page, display=display)
            items = response["items"]
            if not items:
                break

            for item in items:
                normalized = normalize_policy(item)
                policy_id = normalized.get("policy_id")
                if not policy_id or policy_id in seen:
                    continue
                if not normalized.get("title") or not (
                    normalized.get("description") or normalized.get("detail")
                ):
                    continue
                saved.append(save_policy_json(item, output_dir))
                seen.add(str(policy_id))
                query_saved += 1
                if len(saved) >= max_items or (per_query is not None and query_saved >= per_query):
                    break
            page += 1
            if page > 10 or (per_query is not None and query_saved >= per_query):
                break

        if len(saved) >= max_items:
            break

    return saved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-items", type=int, default=60)
    parser.add_argument("--display", type=int, default=10)
    parser.add_argument("--output-dir", default="data/policies")
    parser.add_argument("--query", action="append", dest="queries")
    parser.add_argument("--per-query", type=int)
    args = parser.parse_args()

    saved = collect(
        max_items=args.max_items,
        display=args.display,
        output_dir=args.output_dir,
        queries=args.queries,
        per_query=args.per_query,
    )
    print(json.dumps({"saved_count": len(saved), "files": [str(p) for p in saved]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
