from __future__ import annotations

import re
from typing import Any

from clients.ontong_api import fetch_policies, normalize_policy


def policy_search(profile: dict[str, Any], query: str) -> dict[str, Any]:
    from core.rag import search

    api_response = fetch_policies(query=query, page=1, display=10)
    candidates = [normalize_policy(item) for item in api_response["items"]]
    chunks = search("policies", query, k=5)
    matched = [
        candidate["policy_id"]
        for candidate in candidates
        if _is_profile_match(profile, candidate)
    ]
    return {
        "candidates": candidates,
        "chunks": chunks,
        "matched": matched,
    }


def _is_profile_match(profile: dict[str, Any], policy: dict[str, Any]) -> bool:
    return _age_matches(profile.get("age"), policy) and _region_matches(profile.get("region"), policy.get("region"))


def _age_matches(age: Any, policy: dict[str, Any]) -> bool:
    if age in (None, ""):
        return True
    age_int = int(age)
    min_age = policy.get("min_age")
    max_age = policy.get("max_age")
    if min_age is not None and age_int < int(min_age):
        return False
    if max_age is not None and age_int > int(max_age):
        return False
    return True


def _region_matches(user_region: Any, policy_region: Any) -> bool:
    if not user_region or not policy_region:
        return True
    user = _normalize_region(str(user_region))
    policy = _normalize_region(str(policy_region))
    return user in policy or policy in user or "전국" in policy


def _normalize_region(value: str) -> str:
    value = re.sub(r"\s+", "", value)
    value = value.replace("특별시", "").replace("광역시", "").replace("특별자치시", "")
    value = value.replace("특별자치도", "").replace("자치도", "").replace("도", "")
    return value
