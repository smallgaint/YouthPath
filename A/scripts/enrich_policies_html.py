"""Fetch policy detail pages and extract main body text with trafilatura.

Saves one .txt file per policy under data/policies_html/{policy_id}.txt.
Polite crawling: per-domain sequential, 1.5s sleep between same-domain requests,
clear User-Agent, single retry on failure.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import trafilatura


USER_AGENT = "YouthPathProject/1.0 (Hanyang University Data Science Project; contact: hanyanglaba@gmail.com)"
DEFAULT_HTML_DIR = Path("data/policies_html")
DEFAULT_LOG_PATH = Path("data/policies_html/_crawl_log.json")
DEFAULT_TIMEOUT = 15.0
PER_DOMAIN_SLEEP = 1.5
MAX_RETRY = 1


def load_targets(data_dir: str = "data/policies") -> list[dict[str, Any]]:
    targets = []
    for path in sorted(Path(data_dir).glob("*.json")):
        policy = json.loads(path.read_text(encoding="utf-8"))
        raw = policy.get("raw") or {}
        url = raw.get("REF_URL_ADDR1") or policy.get("link") or ""
        if not url:
            continue
        targets.append(
            {
                "policy_id": policy["policy_id"],
                "title": policy.get("title") or "",
                "url": url,
                "domain": urlparse(url).netloc,
            }
        )
    return targets


def pick_diverse_sample(targets: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in targets:
        by_domain[t["domain"]].append(t)
    domains_sorted = sorted(by_domain.keys(), key=lambda d: -len(by_domain[d]))
    sample = []
    for domain in domains_sorted:
        if len(sample) >= n:
            break
        sample.append(by_domain[domain][0])
    return sample


def fetch_and_extract(target: dict[str, Any], client: httpx.Client) -> dict[str, Any]:
    url = target["url"]
    last_error = ""
    for attempt in range(MAX_RETRY + 1):
        try:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
            html = response.text
            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                favor_recall=True,
            )
            return {
                "policy_id": target["policy_id"],
                "url": url,
                "domain": target["domain"],
                "status": response.status_code,
                "content_length": len(html),
                "extracted_length": len(extracted) if extracted else 0,
                "ok": bool(extracted and len(extracted) >= 50),
                "extracted": extracted or "",
                "error": "",
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"[:200]
            if attempt < MAX_RETRY:
                time.sleep(2.0)
                continue
    return {
        "policy_id": target["policy_id"],
        "url": url,
        "domain": target["domain"],
        "status": 0,
        "content_length": 0,
        "extracted_length": 0,
        "ok": False,
        "extracted": "",
        "error": last_error,
    }


def crawl(
    targets: list[dict[str, Any]],
    out_dir: Path,
    log_path: Path,
    skip_existing: bool = True,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    last_request_per_domain: dict[str, float] = {}
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

    results: list[dict[str, Any]] = []
    with httpx.Client(timeout=DEFAULT_TIMEOUT, headers=headers) as client:
        for i, target in enumerate(targets, 1):
            out_file = out_dir / f"{target['policy_id']}.txt"
            if skip_existing and out_file.exists():
                results.append(
                    {
                        "policy_id": target["policy_id"],
                        "url": target["url"],
                        "domain": target["domain"],
                        "status": 0,
                        "extracted_length": out_file.stat().st_size,
                        "ok": True,
                        "error": "",
                        "cached": True,
                    }
                )
                print(f"[{i:3d}/{len(targets)}] CACHE {target['policy_id']}")
                continue

            domain = target["domain"]
            last = last_request_per_domain.get(domain, 0.0)
            wait = PER_DOMAIN_SLEEP - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)

            result = fetch_and_extract(target, client)
            last_request_per_domain[domain] = time.monotonic()

            if result["ok"]:
                out_file.write_text(result["extracted"], encoding="utf-8")
            result.pop("extracted", None)
            results.append(result)

            mark = "OK   " if result["ok"] else "FAIL "
            err = f" err={result['error']}" if result["error"] else ""
            print(
                f"[{i:3d}/{len(targets)}] {mark} {target['policy_id']} "
                f"len={result['extracted_length']} {domain}{err}"
            )

    summary = {
        "total": len(results),
        "ok": sum(1 for r in results if r["ok"]),
        "fail": sum(1 for r in results if not r["ok"]),
        "by_domain": _summarize_by_domain(results),
        "results": results,
    }
    log_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _summarize_by_domain(results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    by_domain: dict[str, dict[str, int]] = defaultdict(lambda: {"ok": 0, "fail": 0})
    for r in results:
        by_domain[r["domain"]]["ok" if r["ok"] else "fail"] += 1
    return dict(by_domain)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/policies")
    parser.add_argument("--out-dir", default=str(DEFAULT_HTML_DIR))
    parser.add_argument("--log", default=str(DEFAULT_LOG_PATH))
    parser.add_argument("--sample", type=int, default=0, help="Crawl only N diverse-domain samples")
    parser.add_argument("--policy-ids", default="", help="Comma-separated policy_ids to crawl")
    parser.add_argument("--no-cache", action="store_true", help="Re-fetch even if cached")
    args = parser.parse_args()

    targets = load_targets(args.data_dir)

    if args.policy_ids:
        wanted = set(args.policy_ids.split(","))
        targets = [t for t in targets if t["policy_id"] in wanted]
    elif args.sample:
        targets = pick_diverse_sample(targets, args.sample)

    if not targets:
        print("No targets to crawl.")
        return

    summary = crawl(
        targets,
        out_dir=Path(args.out_dir),
        log_path=Path(args.log),
        skip_existing=not args.no_cache,
    )
    print()
    print(f"=== Summary ===")
    print(f"OK:   {summary['ok']}/{summary['total']}")
    print(f"FAIL: {summary['fail']}/{summary['total']}")
    print(f"By domain:")
    for domain, counts in sorted(summary["by_domain"].items(), key=lambda x: -(x[1]['ok'] + x[1]['fail'])):
        print(f"  {counts['ok']:3d} OK / {counts['fail']:3d} FAIL  {domain}")


if __name__ == "__main__":
    main()
