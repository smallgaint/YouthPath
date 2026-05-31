from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


BASE_URL = "https://www.youthcenter.go.kr/go/ythip/getPlcy"
LEGACY_BASE_URL = "https://www.youthcenter.go.kr/opi/youthPlcyList.do"
PORTAL_SEARCH_URL = "https://www.youthcenter.go.kr/pubot/search/portalPolicySearch"


FIELD_ALIASES = {
    "policy_id": ["DOCID", "plcyNo", "polyBizSjnm", "bizId", "policyId", "id"],
    "title": ["PLCY_NM", "plcyNm", "polyBizSjnm", "policyName", "title", "name"],
    "description": ["PLCY_EXPLN_CN", "PLCY_SPRT_CN", "plcySprtCn", "polyItcnCn", "description", "content"],
    "detail": ["PLCY_APLY_MTHD_CN", "PLCY_SPRT_CN", "plcyExplnCn", "sporCn", "detail", "cnsgNmor"],
    "region": ["STDG_NM", "zipCd", "region", "lclsfNm", "polyRlmCd", "area"],
    "category": ["USER_LCLSF_NM", "USER_MCLSF_NM", "mclsfNm", "lclsfNm", "bizTycdSel", "srchPolyBizSecd", "category"],
    "min_age": ["SPRT_TRGT_MIN_AGE", "sprtTrgtMinAge", "ageInfo", "minAge"],
    "max_age": ["SPRT_TRGT_MAX_AGE", "sprtTrgtMaxAge", "ageInfo", "maxAge"],
    "income": ["EARN_ETC_CN", "EARN_MIN_AMT", "EARN_CND_CN", "earnCndCn", "income", "incomeInfo"],
    "deadline": ["APLY_PRD_END_YMD", "APLY_PRD_SE_CD", "aplyYmd", "rqutPrdCn", "deadline", "applyPeriod"],
    "link": ["APLY_URL_ADDR", "REF_URL_ADDR1", "aplyUrlAddr", "rfcSiteUrla1", "link", "url"],
}


def get_api_key() -> str:
    load_dotenv()
    key = os.getenv("ONTONG_API_KEY", "").strip()
    if not key:
        raise RuntimeError("ONTONG_API_KEY is missing. Put it in .env first.")
    return key


def fetch_policies(
    query: str | None = None,
    page: int = 1,
    display: int = 10,
    *,
    category_code: str | None = None,
    keywords: str | None = None,
    api_key: str | None = None,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Call Ontong Youth policy API.

    The current official endpoint accepts apiKeyNm, pageNum, pageSize and
    rtnType. The older documented youthPlcyList.do endpoint is retained as a
    secondary attempt, and the public web JSON search is the final fallback.
    """
    params: dict[str, Any] = {
        "apiKeyNm": api_key or get_api_key(),
        "pageNum": page,
        "pageSize": display,
        "rtnType": "json",
    }
    if query:
        params["plcyNm"] = query
    if category_code:
        params["lclsfNm"] = category_code
    if keywords:
        params["plcyKywdNm"] = keywords

    headers = {
        "Accept": "application/json, application/xml;q=0.9, text/xml;q=0.8",
        "User-Agent": "Mozilla/5.0 YouthPathProject/1.0",
    }
    with httpx.Client(timeout=timeout, headers=headers) as client:
        response = client.get(BASE_URL, params=params)
        try:
            response.raise_for_status()
            parsed = parse_response(response.text)
            if parsed["items"]:
                return parsed
        except httpx.HTTPError:
            pass

        legacy_params: dict[str, Any] = {
            "openApiVlak": api_key or get_api_key(),
            "pageIndex": page,
            "display": display,
        }
        if query:
            legacy_params["query"] = query
        if category_code:
            legacy_params["bizTycdSel"] = category_code
        if keywords:
            legacy_params["keyword"] = keywords
        legacy_response = client.get(LEGACY_BASE_URL, params=legacy_params)
        if legacy_response.status_code not in {301, 302, 303, 307, 308}:
            try:
                legacy_response.raise_for_status()
                parsed = parse_response(legacy_response.text)
                if parsed["items"]:
                    return parsed
            except httpx.HTTPError:
                pass

    return fetch_portal_policies(query=query, page=page, display=display, timeout=timeout)


def fetch_portal_policies(
    query: str | None = None,
    page: int = 1,
    display: int = 10,
    *,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Fallback used by the official Ontong Youth web search page."""
    payload = {
        "PVSN_INST_GROUP_CD": "",
        "SPRT_TRGT_AGE": "",
        "EARN_MIN_AMT": "",
        "EARN_MAX_AMT": "",
        "QLFC_ACBG_NM": "",
        "MRG_STTS_CD": "",
        "query": query or "",
        "MJR_CND_NM": "",
        "EMPM_STTS_NM": "",
        "STDG_NM": "",
        "SPCL_FLD_NM": "",
        "USER_MCLSF_NO": "",
        "STDG_CTPV_NM": "",
        "PLCY_KYWD_SN": "",
        "pageNum": page,
        "sortFields": "DATE/DESC",
        "listCount": display,
        "searchFields": "all",
        "APLY_PRD_BGNG_YMD": "",
        "APLY_PRD_END_YMD": "",
        "APLY_PRD_SE_CD": "",
        "ODTM_CD": "",
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://www.youthcenter.go.kr/youthPolicy/ythPlcyTotalSearch",
        "User-Agent": "Mozilla/5.0 YouthPathProject/1.0",
    }
    with httpx.Client(timeout=timeout, headers=headers) as client:
        response = client.post(PORTAL_SEARCH_URL, json=payload)
        response.raise_for_status()
        data = response.json()
    items = data.get("searchResult", {}).get("youthpolicy", [])
    return {"raw": data, "items": items}


def parse_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        return {"raw": "", "items": []}

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = _parse_xml(text)

    items = extract_items(data)
    return {"raw": data, "items": items}


def _parse_xml(text: str) -> dict[str, Any]:
    root = ET.fromstring(text)

    def convert(node: ET.Element) -> Any:
        children = list(node)
        if not children:
            return (node.text or "").strip()
        grouped: dict[str, Any] = {}
        for child in children:
            value = convert(child)
            if child.tag in grouped:
                if not isinstance(grouped[child.tag], list):
                    grouped[child.tag] = [grouped[child.tag]]
                grouped[child.tag].append(value)
            else:
                grouped[child.tag] = value
        return grouped

    return {root.tag: convert(root)}


def extract_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []

    for key in ["youthPolicyList", "youthPlcyList", "policyList", "items", "item", "data", "result"]:
        value = data.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
        if isinstance(value, dict):
            nested = extract_items(value)
            if nested:
                return nested

    for value in data.values():
        nested = extract_items(value)
        if nested:
            return nested
    return []


def normalize_policy(policy: dict[str, Any]) -> dict[str, Any]:
    normalized = {field: _first_value(policy, aliases) for field, aliases in FIELD_ALIASES.items()}
    normalized["policy_id"] = _clean_text(normalized.get("policy_id") or normalized.get("title") or "")
    normalized["title"] = _clean_text(normalized.get("title"))
    normalized["description"] = _clean_text(normalized.get("description"))
    normalized["detail"] = _clean_text(normalized.get("detail"))
    normalized["region"] = _clean_text(normalized.get("region"))
    normalized["category"] = _clean_text(normalized.get("category"))
    normalized["income"] = _clean_text(normalized.get("income"))
    normalized["deadline"] = _clean_text(normalized.get("deadline"))
    normalized["link"] = _clean_text(normalized.get("link"))
    normalized["min_age"], normalized["max_age"] = _extract_age_range(
        normalized.get("min_age"),
        normalized.get("max_age"),
        policy,
    )
    normalized["raw"] = policy
    return normalized


def save_policy_json(policy: dict[str, Any], output_dir: str | Path = "data/policies") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    normalized = normalize_policy(policy)
    safe_id = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", normalized["policy_id"])[:80] or "policy"
    path = output_path / f"{safe_id}.json"
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _first_value(policy: dict[str, Any], aliases: list[str]) -> Any:
    for alias in aliases:
        value = policy.get(alias)
        if value not in (None, ""):
            return value
    return None


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = re.sub(r"<[^>]+>", "", str(value))
    return re.sub(r"\s+", " ", text).strip()


def _extract_age_range(
    min_value: Any,
    max_value: Any,
    policy: dict[str, Any],
) -> tuple[int | None, int | None]:
    min_age = _to_int(min_value)
    max_age = _to_int(max_value)
    if min_age is not None or max_age is not None:
        return min_age, max_age

    joined = " ".join(str(v) for v in policy.values() if isinstance(v, (str, int, float)))
    numbers = [int(x) for x in re.findall(r"만?\s*(\d{2})\s*세", joined)]
    if len(numbers) >= 2:
        return min(numbers), max(numbers)
    if len(numbers) == 1:
        return None, numbers[0]
    return None, None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else None
