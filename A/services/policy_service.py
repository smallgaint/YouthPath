from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

try:
    from A.clients.ontong_api import fetch_policies, normalize_policy
except Exception:  # noqa: BLE001
    fetch_policies = None

    def normalize_policy(policy: dict[str, Any]) -> dict[str, Any]:
        return {
            "policy_id": str(policy.get("policy_id") or policy.get("DOCID") or policy.get("id") or policy.get("title") or ""),
            "title": _clean_text(policy.get("title") or policy.get("PLCY_NM") or ""),
            "description": _clean_text(policy.get("description") or policy.get("PLCY_EXPLN_CN") or ""),
            "detail": _clean_text(policy.get("detail") or policy.get("PLCY_SPRT_CN") or ""),
            "region": _clean_text(policy.get("region") or policy.get("STDG_NM") or ""),
            "category": _clean_text(policy.get("category") or policy.get("USER_LCLSF_NM") or ""),
            "min_age": policy.get("min_age") or _to_int(policy.get("SPRT_TRGT_MIN_AGE")),
            "max_age": policy.get("max_age") or _to_int(policy.get("SPRT_TRGT_MAX_AGE")),
            "income": _clean_text(policy.get("income") or policy.get("EARN_ETC_CN") or ""),
            "deadline": _clean_text(policy.get("deadline") or policy.get("APLY_PRD_END_YMD") or ""),
            "link": _clean_text(policy.get("link") or policy.get("APLY_URL_ADDR") or policy.get("REF_URL_ADDR1") or ""),
            "raw": policy.get("raw") if isinstance(policy.get("raw"), dict) else policy,
        }


# ─── 상수 ──────────────────────────────────────────────────────────────────

REGION_CODE_PREFIX: dict[str, str] = {
    "11": "서울", "26": "부산", "27": "대구", "28": "인천",
    "29": "광주", "30": "대전", "31": "울산", "36": "세종",
    "41": "경기", "42": "강원", "43": "충북", "44": "충남",
    "45": "전북", "46": "전남", "47": "경북", "48": "경남",
    "50": "제주", "51": "강원",
}

# (label, raw key 신버전 대문자, raw key 구버전 카멜, 다중값 구분자)
OTHER_CONDITION_FIELDS: list[tuple[str, str, str, str | None]] = [
    ("결혼상태", "MRG_STTS_NM", "mrgSttsNm", "|"),
    ("학력", "QLFC_ACBG_NM", "qlfcAcbgNm", None),
    ("취업상태", "EMPM_STTS_NM", "empmSttsNm", ","),
    ("전공", "MJR_CND_NM", "mjrCndNm", ","),
    ("특화분야", "SPCL_FLD_NM", "spclFldNm", ","),
]

HIGHLIGHT_RE = re.compile(r'<span class="highlight">(.*?)</span>', re.DOTALL)
HTML_TAG_RE = re.compile(r"<[^>]+>")
JUNK_CHARS_RE = re.compile(r"[⃞〇○●□■◎▷▶]")
INCOME_RANGE_RE = re.compile(r"중위소득\s*(\d+)\s*%?\s*~\s*(\d+)\s*%")
INCOME_SINGLE_RE = re.compile(r"중위소득\s*(\d+)\s*%")
YYYYMMDD_RE = re.compile(r"\d{8}")

MIN_SCORE = 0.6
W_AGE = 0.4
W_REGION = 0.3
W_INCOME = 0.3


# ─── 기존 공개 API (변경 없음, 테스트 호환 유지) ─────────────────────────

def policy_search(profile: dict[str, Any], query: str) -> dict[str, Any]:
    from A.core.rag import search

    api_response = _fetch_policies_smart(query, display=10)
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


# ─── 텍스트 정제 ──────────────────────────────────────────────────────────

def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = HIGHLIGHT_RE.sub(r"\1", text)
    text = HTML_TAG_RE.sub("", text)
    text = JUNK_CHARS_RE.sub(" ", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _raw_field(policy: dict[str, Any], *keys: str) -> str:
    raw = policy.get("raw") or {}
    for key in keys:
        value = raw.get(key)
        if value:
            return _clean_text(value)
    return ""


def _ensure_scheme(url: str) -> str:
    if url and not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


# ─── 필드 추출 ────────────────────────────────────────────────────────────

def _summary(policy: dict[str, Any]) -> str:
    text = _clean_text(policy.get("description") or "")
    if not text:
        text = _raw_field(policy, "PLCY_EXPLN_CN", "plcyExplnCn")
    if not text:
        return _clean_text(policy.get("title") or "")
    if len(text) > 80:
        text = text[:80].rstrip() + "..."
    return text


def _benefit(policy: dict[str, Any]) -> str:
    return _raw_field(policy, "PLCY_SPRT_CN", "plcySprtCn")


def _apply_method(policy: dict[str, Any]) -> str:
    return _raw_field(policy, "PLCY_APLY_MTHD_CN", "plcyAplyMthdCn")


def _exclusion(policy: dict[str, Any]) -> str | None:
    text = _raw_field(policy, "PTCP_PRP_TRGT_CN", "ptcpPrpTrgtCn")
    return text or None


def _keywords(policy: dict[str, Any]) -> list[str]:
    text = _raw_field(policy, "PLCY_KYWD_NM", "plcyKywdNm")
    if not text:
        return []
    return [k.strip() for k in text.split(",") if k.strip()]


def _host_org(policy: dict[str, Any]) -> str:
    return _raw_field(policy, "SPRVSN_INST_CD_NM", "sprvsnInstCdNm")


def _category_major(policy: dict[str, Any]) -> str:
    value = _raw_field(policy, "USER_CLSF_NM", "lclsfNm")
    if not value:
        value = _clean_text(policy.get("category") or "")
    if "_" in value:
        value = value.split("_", 1)[0]
    return value or "기타"


# 안내/참고 URL: 보통 로그인 없이 열람 가능한 정보 페이지
_INFO_URL_KEYS = ("REF_URL_ADDR1", "refUrlAddr1", "rfcSiteUrla1", "rfcSiteUrla2", "link")
# 신청 URL: 복지로/정부24/고용24 등 본인인증·로그인을 요구하는 신청 페이지
_APPLY_URL_KEYS = ("APLY_URL_ADDR", "aplyUrlAddr", "rqutUrla")


def _link_with_kind(
    policy: dict[str, Any], chunks_by_pid: dict[str, list[dict[str, Any]]]
) -> tuple[str | None, str]:
    """정책 링크와 종류를 반환한다.

    반환 kind:
      - "info"  : 로그인 없이 보기 쉬운 안내/참고 URL (우선)
      - "apply" : 로그인이 필요한 신청 URL (안내 URL이 없을 때만)
      - ""      : 링크 없음
    """
    # 1순위: 안내/참고 URL (로그인 불필요한 경우가 많음)
    for key in _INFO_URL_KEYS:
        value = _raw_field(policy, key)
        if value and value != "0":
            url = _ensure_scheme(value)
            # youthcenter.go.kr 딥링크는 외부에서 :8080으로 깨져 연결 불가 → 건너뜀
            if "youthcenter.go.kr" in url:
                continue
            return url, "info"
    # 2순위: RAG 청크의 출처 URL도 안내 성격으로 취급
    pid = policy.get("policy_id") or ""
    for chunk in chunks_by_pid.get(pid, []):
        url = (chunk.get("metadata") or {}).get("source_url", "")
        if url:
            return _ensure_scheme(str(url)), "info"
    # 3순위: 신청 URL (로그인 필요 가능성 높음)
    for key in _APPLY_URL_KEYS:
        value = _raw_field(policy, key)
        if value and value != "0":
            return _ensure_scheme(value), "apply"
    return None, ""


def _link(policy: dict[str, Any], chunks_by_pid: dict[str, list[dict[str, Any]]]) -> str | None:
    return _link_with_kind(policy, chunks_by_pid)[0]


def _fetch_policies_smart(query: str, *, display: int = 20) -> dict[str, Any]:
    """정책 검색: 키워드(plcyKywdNm) 우선 + 정책명(plcyNm) 폴백.

    plcyNm은 정책 '이름' 정확매칭이라 자연어 문장에서 0건이 되기 쉽다.
    plcyKywdNm 키워드 검색이 문장에도 훨씬 견고하므로 이를 1순위로 쓴다.
    """
    if fetch_policies is None:  # type: ignore[truthy-function]
        raise RuntimeError("Ontong API client dependencies are unavailable")
    by_keyword = fetch_policies(query=None, keywords=query, page=1, display=display)
    if by_keyword.get("items"):
        return by_keyword
    return fetch_policies(query=query, page=1, display=display)


def _search_fallback_url(title: str) -> str:
    """로그인 없이 열람 가능한 정부24 통합검색 폴백 URL.

    온통청년 포털 딥링크는 외부에서 :8080으로 리다이렉트되어 동작하지 않으므로,
    안내 URL이 없는 정책은 정책명으로 정부24를 검색하도록 한다.
    """
    title = (title or "").strip()
    if not title:
        return ""
    return "https://www.gov.kr/search?srhQuery=" + quote(title)


def _build_other_conditions(policy: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    raw = policy.get("raw") or {}
    for label, old_key, new_key, sep in OTHER_CONDITION_FIELDS:
        text = _clean_text(raw.get(old_key) or raw.get(new_key) or "")
        if not text:
            continue
        if sep:
            parts = [p.strip() for p in text.split(sep) if p.strip()]
            non_default = [p for p in parts if "제한없음" not in p]
            if not non_default:
                continue
            display = ", ".join(non_default)
        else:
            if "제한없음" in text:
                continue
            display = text
        out.append({"label": label, "required": display})

    extra = _clean_text(raw.get("ADD_APLY_QLFC_CND_CN") or raw.get("addAplyQlfcCndCn") or "")
    if extra and "제한없음" not in extra:
        out.append({"label": "기타", "required": extra})
    return out


# ─── 마감일 / 소득 / 지역 정규화 ──────────────────────────────────────────

def _parse_deadline(policy: dict[str, Any]) -> tuple[str | None, str, str]:
    raw_str = str(policy.get("deadline") or "")
    raw = policy.get("raw") or {}

    matches = YYYYMMDD_RE.findall(raw_str)
    for ymd in reversed(matches):
        try:
            iso = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]}"
            datetime.strptime(iso, "%Y-%m-%d")
            return iso, "마감일", raw_str
        except ValueError:
            continue

    period_code = str(raw.get("APLY_PRD_SE_CD") or raw.get("aplyPrdSeCd") or "")
    biz_etc = str(raw.get("BIZ_PRD_ETC_CN") or raw.get("bizPrdEtcCn") or "")
    if "상시" in period_code or "연중" in biz_etc:
        return None, "상시", raw_str

    return None, "미정", raw_str


def _extract_income_ceiling(policy: dict[str, Any]) -> int | None:
    text = _raw_field(policy, "EARN_ETC_CN", "earnEtcCn")
    if not text:
        text = _clean_text(policy.get("income") or "")
    if not text:
        return None

    match = INCOME_RANGE_RE.search(text)
    if match:
        return int(match.group(2))
    match = INCOME_SINGLE_RE.search(text)
    if match:
        return int(match.group(1))
    return None


def _resolve_region(region: str) -> tuple[str, bool]:
    """(label, resolved) 반환. resolved=False면 코드→한글 변환 실패."""
    if not region:
        return "전국", True
    parts = [p.strip() for p in region.split(",") if p.strip()]
    if not parts:
        return "전국", True
    first = parts[0]
    if first.isdigit():
        sido = REGION_CODE_PREFIX.get(first[:2])
        if sido is None:
            label = first
            resolved = False
        else:
            label = sido
            resolved = True
    else:
        label = first
        resolved = True
    if len(parts) > 1:
        label = f"{label} 외 {len(parts) - 1}곳"
    return label, resolved


def _region_matches_any(user_region: str, parts: list[str]) -> bool:
    user_norm = _normalize_region(user_region)
    for part in parts:
        if part.isdigit():
            sido = REGION_CODE_PREFIX.get(part[:2], "")
            if not sido:
                continue
            sido_norm = _normalize_region(sido)
            if user_norm in sido_norm or sido_norm in user_norm:
                return True
        else:
            part_norm = _normalize_region(part)
            if user_norm in part_norm or part_norm in user_norm or "전국" in part_norm:
                return True
    return False


# ─── 점수 계산 ────────────────────────────────────────────────────────────

def _score_age(user_age: Any, policy: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    min_age = policy.get("min_age")
    max_age = policy.get("max_age")

    is_unbounded = (
        (not min_age)
        and (not max_age or (isinstance(max_age, int) and max_age >= 999))
    )

    if is_unbounded:
        required = "나이무관"
    elif min_age and max_age:
        required = f"{int(min_age)}~{int(max_age)}세"
    elif max_age:
        required = f"{int(max_age)}세 이하"
    elif min_age:
        required = f"{int(min_age)}세 이상"
    else:
        required = "나이무관"

    user_str = f"{user_age}세" if user_age not in (None, "") else "미입력"

    if is_unbounded:
        return W_AGE, {"label": "나이", "required": required, "user_value": user_str, "ok": True}
    if user_age in (None, ""):
        return 0.0, {"label": "나이", "required": required, "user_value": "미입력", "ok": False}

    age_int = int(user_age)
    lower = int(min_age) if min_age else 0
    upper = int(max_age) if max_age else 999
    in_range = lower <= age_int <= upper
    score = W_AGE if in_range else 0.0
    return score, {"label": "나이", "required": required, "user_value": user_str, "ok": in_range}


def _score_region(user_region: Any, policy: dict[str, Any]) -> tuple[float, dict[str, Any], bool]:
    """(score, criterion, unresolved) 반환."""
    region_raw = str(policy.get("region") or "")
    label, resolved = _resolve_region(region_raw)
    user_str = str(user_region) if user_region else "미입력"

    parts = [p.strip() for p in region_raw.split(",") if p.strip()]
    is_national = not parts or any("전국" in p for p in parts)

    if is_national:
        return W_REGION, {"label": "지역", "required": "전국", "user_value": user_str, "ok": True}, False

    if not user_region:
        return 0.0, {"label": "지역", "required": label, "user_value": "미입력", "ok": False}, not resolved

    if not resolved:
        return W_REGION * 0.5, {"label": "지역", "required": label, "user_value": user_str, "ok": False}, True

    matched = _region_matches_any(str(user_region), parts)
    score = W_REGION if matched else 0.0
    return score, {"label": "지역", "required": label, "user_value": user_str, "ok": matched}, False


def _score_income(user_bracket: Any, policy: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    ceiling = _extract_income_ceiling(policy)
    user_str = f"중위 {user_bracket}%" if user_bracket not in (None, "") else "미입력"

    if ceiling is None:
        return W_INCOME * 0.5, {
            "label": "소득", "required": "확인 불가", "user_value": user_str, "ok": False,
        }

    required = f"중위소득 {ceiling}% 이하"
    if user_bracket in (None, ""):
        return 0.0, {"label": "소득", "required": required, "user_value": "미입력", "ok": False}

    user_int = int(user_bracket)
    ok = user_int <= ceiling
    score = W_INCOME if ok else 0.0
    return score, {"label": "소득", "required": required, "user_value": f"중위 {user_int}%", "ok": ok}


# ─── 표준 Agent 응답 ──────────────────────────────────────────────────────

def build_policy_response(profile: dict[str, Any], query: str) -> dict[str, Any]:
    """Policy Agent 표준 응답을 만든다.

    스키마: docs/policy_agent_response.schema.json

    profile 예: {"age": 27, "region": "서울", "income_bracket": 60}
      - age (int|None): 만 나이
      - region (str|None): 시도명 한글 (예 "서울", "경기")
      - income_bracket (int|None): 본인이 속한 중위소득 % 상한
    """
    from A.core.rag import search

    started = time.perf_counter()
    error: str | None = None
    sources: list[str] = []
    api_path = "none"

    # 1) 온통청년 API
    candidates: list[dict[str, Any]] = []
    try:
        if fetch_policies is None:
            raise RuntimeError("Ontong API client dependencies are unavailable")
        api_response = _fetch_policies_smart(query, display=20)
        candidates = [normalize_policy(item) for item in api_response.get("items", [])]
        if candidates:
            api_path = "official"
            sources.append("온통청년 getPlcy API")
    except Exception as exc:  # noqa: BLE001
        error = f"API 호출 실패: {exc}"

    # 2) RAG
    chunks: list[dict[str, Any]] = []
    try:
        chunks = search("policies", query, k=10)
        if chunks:
            sources.append("Chroma policies")
    except Exception as exc:  # noqa: BLE001
        msg = f"RAG 검색 실패: {exc}"
        error = msg if error is None else f"{error}; {msg}"

    chunks_by_pid: dict[str, list[dict[str, Any]]] = {}
    for chunk in chunks:
        pid = (chunk.get("metadata") or {}).get("policy_id", "")
        if pid:
            chunks_by_pid.setdefault(pid, []).append(chunk)

    api_pids = {c.get("policy_id") for c in candidates if c.get("policy_id")}
    rag_pids = set(chunks_by_pid.keys())

    # API가 비었으면 RAG 청크 metadata로 candidate 합성
    if not candidates and rag_pids:
        for pid in rag_pids:
            md = chunks_by_pid[pid][0].get("metadata") or {}
            min_age = md.get("min_age")
            max_age = md.get("max_age")
            candidates.append({
                "policy_id": pid,
                "title": md.get("title", ""),
                "description": "",
                "detail": "",
                "region": md.get("region", ""),
                "category": md.get("category", ""),
                "min_age": min_age if isinstance(min_age, int) and min_age >= 0 else None,
                "max_age": max_age if isinstance(max_age, int) and max_age >= 0 else None,
                "income": "",
                "deadline": md.get("deadline", ""),
                "link": md.get("source_url", ""),
                "raw": {},
            })

    # 3) 오프라인 E2E 폴백: API 키/네트워크/RAG 인덱스가 없어도 로컬 수집 JSON으로 정책 분기를 검증한다.
    if not candidates:
        local_candidates = _load_local_policy_candidates(query, limit=40)
        if local_candidates:
            candidates = local_candidates
            api_path = "local-json"
            sources.append("A/data/policies/*.json")

    items: list[dict[str, Any]] = []
    region_unresolved = 0
    seen_pids: set[str] = set()

    for cand in candidates:
        pid = cand.get("policy_id") or ""
        if pid in seen_pids:
            continue
        seen_pids.add(pid)

        age_score, age_crit = _score_age(profile.get("age"), cand)
        region_score, region_crit, region_un = _score_region(profile.get("region"), cand)
        if region_un:
            region_unresolved += 1
        income_score, income_crit = _score_income(profile.get("income_bracket"), cand)

        score = round(age_score + region_score + income_score, 3)
        if score < MIN_SCORE:
            continue

        matched: list[dict[str, Any]] = []
        unmatched: list[dict[str, Any]] = []
        for crit in (age_crit, region_crit, income_crit):
            (matched if crit["ok"] else unmatched).append(crit)

        deadline, deadline_type, deadline_raw = _parse_deadline(cand)
        
        if deadline:
            try:
                if datetime.strptime(deadline, "%Y-%m-%d").date() < datetime.today().date():
                    continue
            except ValueError:
                pass

        if pid in api_pids and pid in rag_pids:
            src = "api+rag"
        elif pid in api_pids:
            src = "api"
        else:
            src = "rag"

        link_url, link_kind = _link_with_kind(cand, chunks_by_pid)
        # 로그인 없는 안내 링크가 없으면(신청 URL만 있거나 링크 없음) 정부24 검색 폴백 제공
        title_text = _clean_text(cand.get("title") or "")
        search_url = _search_fallback_url(title_text) if link_kind != "info" else ""

        items.append({
            "policy_id": pid,
            "title": _clean_text(cand.get("title") or ""),
            "summary": _summary(cand),
            "benefit": _benefit(cand),
            "region_label": region_crit["required"],
            "category": _category_major(cand),
            "keywords": _keywords(cand),
            "host_org": _host_org(cand),
            "deadline": deadline,
            "deadline_type": deadline_type,
            "deadline_raw": deadline_raw,
            "score": score,
            "matched_criteria": matched,
            "unmatched_criteria": unmatched,
            "other_conditions": _build_other_conditions(cand),
            "apply_method": _apply_method(cand),
            "exclusion": _exclusion(cand),
            "link": link_url,
            "link_kind": link_kind,
            "search_url": search_url,
            "source": src,
        })

    items.sort(key=lambda x: x["score"], reverse=True)
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    return {
        "agent_name": "policy",
        "items": items,
        "sources": sources,
        "metadata": {
            "latency_ms": elapsed_ms,
            "query": query,
            "candidate_count": len(candidates),
            "matched_count": len(items),
            "api_path": api_path,
            "region_unresolved": region_unresolved,
        },
        "error": error,
    }


def _load_local_policy_candidates(query: str, limit: int = 40) -> list[dict[str, Any]]:
    policy_dir = Path(__file__).resolve().parents[1] / "data" / "policies"
    if not policy_dir.exists():
        return []
    query_tokens = [token for token in re.split(r"\s+", _clean_text(query)) if token]
    rows: list[tuple[int, dict[str, Any]]] = []
    for path in policy_dir.glob("*.json"):
        try:
            policy = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        searchable = " ".join(
            _clean_text(policy.get(key) or "")
            for key in ["title", "description", "detail", "region", "category", "income"]
        )
        hit_count = sum(1 for token in query_tokens if token in searchable)
        if hit_count or not query_tokens:
            rows.append((hit_count, normalize_policy(policy)))
    rows.sort(key=lambda row: row[0], reverse=True)
    return [policy for _, policy in rows[:limit]]
