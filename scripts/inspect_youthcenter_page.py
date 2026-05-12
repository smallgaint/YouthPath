from __future__ import annotations

import re

import httpx


def main() -> None:
    url = "https://www.youthcenter.go.kr/youthPolicy/ythPlcyTotalSearch"
    response = httpx.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    print(response.status_code, response.url, len(response.text))

    patterns = [
        r"""(?i)(?:url|href|action)\s*[=:]\s*["']([^"']+)""",
        r"""(?i)\$\.ajax\(\{[^}]+""",
        r"""(?i)fetch\(["']([^"']+)""",
    ]
    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, response.text):
            text = match.group(1) if match.lastindex else match.group(0)
            if text in seen:
                continue
            seen.add(text)
            if any(key in text for key in ["Plcy", "plcy", "Policy", "policy", "youth", "Youth"]):
                print(text[:500])


if __name__ == "__main__":
    main()
