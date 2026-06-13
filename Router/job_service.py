from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests

from Router.schemas import AgentResult


def _load_env_file() -> None:
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    env_path = next((path for path in candidates if path.exists()), None)
    if env_path is None:
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        return


def _worknet_key(env_name: str) -> str:
    return (os.getenv(env_name) or os.getenv("WORKNET_API_KEY") or "").strip()


_load_env_file()

WORKNET_KEYS = {
    "채용정보": _worknet_key("WORKNET_RECRUIT_API_KEY"),
    "강소기업": _worknet_key("WORKNET_SME_API_KEY"),
    "직무정보": _worknet_key("WORKNET_JOB_INFO_API_KEY"),
    "공통코드": _worknet_key("WORKNET_COMMON_CODE_API_KEY"),
    "직업정보": _worknet_key("WORKNET_OCCUPATION_API_KEY"),
}

WORKNET_BASE = os.getenv("WORKNET_BASE_URL", "https://www.work24.go.kr/cm/openApi/call")
WORKNET_TIMEOUT = float(os.getenv("WORKNET_TIMEOUT", "6"))
WORKNET_PATHS = {
    "채용정보": os.getenv("WORKNET_RECRUIT_PATH", "/wk/callOpenApiSvcInfo210L01.do"),
    "강소기업": os.getenv("WORKNET_SME_PATH", "/wk/callOpenApiSmeList.do"),
    "직무정보": os.getenv("WORKNET_JOB_INFO_PATH", "/wk/callOpenApiJobInfo.do"),
    "공통코드": os.getenv("WORKNET_COMMON_CODE_PATH", "/wk/callOpenApiCommonCode.do"),
    "직업정보": os.getenv("WORKNET_OCCUPATION_PATH", "/wk/callOpenApiOccupation.do"),
}

REGION_CODES = {
    "서울": "11",
    "부산": "26",
    "대구": "27",
    "인천": "28",
    "광주": "29",
    "대전": "30",
    "울산": "31",
    "세종": "36",
    "경기": "41",
    "강원": "51",
    "충북": "43",
    "충남": "44",
    "전북": "52",
    "전남": "46",
    "경북": "47",
    "경남": "48",
    "제주": "50",
}

JOB_CODE_HINTS = {
    "데이터": "2236",
    "분석": "2236",
    "ai": "2236",
    "인공지능": "2236",
    "백엔드": "1332",
    "backend": "1332",
    "개발": "1332",
    "프론트": "1331",
    "frontend": "1331",
    "마케팅": "0241",
    "디자인": "4154",
}


MOCK_WORKNET_RESPONSE = [
    {
        "wantedAuthNo": "K162345789",
        "title": "데이터분석 신입 채용",
        "company": "○○데이터",
        "bizNo": "123-45-67890",
        "region": "서울 강남구",
        "regionCd": "11",
        "jobsCd": "2236",
        "career": "신입",
        "minEdubg": "대졸",
        "salTpNm": "연봉",
        "sal": "3500",
        "regDt": "2026-05-08",
        "closeDt": "2026-05-20",
    },
    {
        "wantedAuthNo": "K162345790",
        "title": "주니어 데이터 분석가",
        "company": "△△테크",
        "bizNo": "234-56-78901",
        "region": "서울 판교",
        "regionCd": "11",
        "jobsCd": "2236",
        "career": "신입",
        "minEdubg": "대졸",
        "salTpNm": "연봉",
        "sal": "3800",
        "regDt": "2026-05-09",
        "closeDt": "2026-05-25",
    },
]

MOCK_JOB_SKILLS = {
    "2236": {
        "required_skills": ["Python", "SQL", "통계 기초"],
        "preferred_skills": ["Tableau", "추천 시스템"],
    }
}


def run_job_agent(profile: dict[str, Any], query: str) -> dict[str, Any]:
    t_start = datetime.now()
    raw_jobs: list[dict[str, Any]] = []
    backend = "mock"
    error: str | None = None
    api_calls = {"채용정보": 0, "직무정보": 0}

    try:
        raw_jobs = _search_worknet_jobs(profile, query)
        api_calls["채용정보"] = 1
        if raw_jobs:
            backend = "worknet"
    except Exception as exc:  # noqa: BLE001
        error = f"Worknet live search failed: {exc}"

    if not raw_jobs:
        raw_jobs = MOCK_WORKNET_RESPONSE

    candidates = [_normalize(row) for row in raw_jobs]

    for candidate in candidates:
        skills = _get_job_skills(candidate["job_code"], profile, query, backend=backend)
        if backend == "worknet":
            api_calls["직무정보"] += 1
        candidate["required_skills"] = skills["required_skills"]
        candidate["preferred_skills"] = skills["preferred_skills"]
        candidate["is_strong_sme"] = candidate["company_bizno"] in {"123-45-67890", "234-56-78901"}
        candidate["fit_score"], candidate["fit_breakdown"] = _compute_fit_score(profile, candidate)

    candidates.sort(key=lambda item: item["fit_score"], reverse=True)

    return AgentResult(
        agent_name="job",
        items=candidates[:5],
        sources=[
            f"{backend}:worknet:채용정보",
            f"{backend}:worknet:직무정보",
            "router:job-code-region-mapping",
        ],
        metadata={
            "latency_ms": int((datetime.now() - t_start).total_seconds() * 1000),
            "api_calls": api_calls,
            "backend": backend,
            "partial": backend != "worknet",
            "note": "Worknet live pipeline is attempted first; sample data is used only as fallback.",
            "query": query,
        },
        error=error,
    ).to_dict()


def _search_worknet_jobs(profile: dict[str, Any], query: str) -> list[dict[str, Any]]:
    if not WORKNET_KEYS["채용정보"]:
        raise ValueError("WORKNET_RECRUIT_API_KEY or WORKNET_API_KEY is required for Worknet live search.")

    params = {
        "authKey": WORKNET_KEYS["채용정보"],
        "returnType": "JSON",
        "startPage": 1,
        "display": 20,
        "keyword": profile.get("target_role") or query,
    }
    region_code = _region_code(profile.get("region"))
    job_code = _job_code(profile.get("target_role") or query)
    if region_code:
        params["region"] = region_code
        params["regionCd"] = region_code
    if job_code:
        params["occupation"] = job_code
        params["jobsCd"] = job_code

    response = requests.get(
        f"{WORKNET_BASE}{WORKNET_PATHS['채용정보']}",
        params=params,
        timeout=WORKNET_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return _extract_job_rows(data)


def _extract_job_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if not isinstance(data, dict):
        return []

    for key in ["wanted", "wantedRoot", "jobs", "job", "items", "item", "data", "result", "list"]:
        value = data.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, dict):
            nested = _extract_job_rows(value)
            if nested:
                return nested
    for value in data.values():
        nested = _extract_job_rows(value)
        if nested:
            return nested
    return []


def _get_job_skills(job_code: str, profile: dict[str, Any], query: str, *, backend: str) -> dict[str, list[str]]:
    fallback = MOCK_JOB_SKILLS.get(job_code) or _infer_job_skills(profile.get("target_role") or query)
    if backend != "worknet" or not job_code:
        return fallback
    if not WORKNET_KEYS["직무정보"]:
        return fallback

    try:
        response = requests.get(
            f"{WORKNET_BASE}{WORKNET_PATHS['직무정보']}",
            params={
                "authKey": WORKNET_KEYS["직무정보"],
                "returnType": "JSON",
                "jobCd": job_code,
                "jobsCd": job_code,
            },
            timeout=4,
        )
        response.raise_for_status()
        text = response.text
    except Exception:
        return fallback

    skill_text = text.lower()
    required = [skill for skill in fallback["required_skills"] if skill.lower() in skill_text]
    preferred = [skill for skill in fallback["preferred_skills"] if skill.lower() in skill_text]
    return {
        "required_skills": required or fallback["required_skills"],
        "preferred_skills": preferred or fallback["preferred_skills"],
    }


def _infer_job_skills(text: Any) -> dict[str, list[str]]:
    lowered = str(text).lower()
    if any(keyword in lowered for keyword in ["데이터", "분석", "ai", "인공지능"]):
        return {"required_skills": ["Python", "SQL", "통계 기초"], "preferred_skills": ["머신러닝", "Tableau"]}
    if any(keyword in lowered for keyword in ["백엔드", "backend", "개발"]):
        return {"required_skills": ["Python", "FastAPI", "SQL"], "preferred_skills": ["Docker", "AWS"]}
    return {"required_skills": ["문제 해결", "협업"], "preferred_skills": ["프로젝트 경험"]}


def _region_code(region: Any) -> str:
    region_text = str(region or "")
    for label, code in REGION_CODES.items():
        if label in region_text:
            return code
    return ""


def _job_code(text: Any) -> str:
    lowered = str(text or "").lower()
    for keyword, code in JOB_CODE_HINTS.items():
        if keyword in lowered:
            return code
    return ""


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    deadline = _first(raw, "closeDt", "close_dt", "wantedInfoCloseDt", "receiptCloseDt", "deadline")
    wanted_auth_no = _first(raw, "wantedAuthNo", "wanted_auth_no", "wantedAuthNoStr", "id")
    return {
        "wantedAuthNo": wanted_auth_no,
        "title": str(_first(raw, "title", "wantedTitle", "wantedInfoTitle", "jobNm", "recrutPbancTtl")).strip(),
        "company": str(_first(raw, "company", "corpNm", "companyNm", "businoNm", "empName")).strip(),
        "company_bizno": _first(raw, "bizNo", "busino", "companyBizNo"),
        "is_strong_sme": False,
        "location": _first(raw, "region", "regionNm", "basicAddr", "workRegion", "loc"),
        "region_code": _first(raw, "regionCd", "region_code"),
        "job_code": _first(raw, "jobsCd", "jobCd", "occupation", "jobsCdNm"),
        "deadline": deadline,
        "days_remaining": _days_until(deadline),
        "posted_at": _first(raw, "regDt", "regDtHm", "wantedInfoRegDt", "posted_at"),
        "career_required": _first(raw, "career", "careerNm", "careerCondition", "career_required"),
        "education_required": _first(raw, "minEdubg", "education", "education_required"),
        "salary": {
            "type": _first(raw, "salTpNm", "salaryType"),
            "value": _to_int(_first(raw, "sal", "salary", "salDesc", default=0)),
            "unit": "만원",
        },
        "required_skills": [],
        "preferred_skills": [],
        "fit_score": 0.0,
        "fit_breakdown": {},
        "source": "worknet",
        "url": _first(raw, "wantedInfoUrl", "url", "link")
        or f"https://www.work.go.kr/empSpt/empSrch/empSrchView.do?wantedAuthNo={wanted_auth_no}",
    }


def _first(raw: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = raw.get(key)
        if value not in (None, ""):
            return value
    return default


def _compute_fit_score(profile: dict[str, Any], job: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    breakdown: dict[str, Any] = {}
    score = 0.0

    user_skills = {str(skill).lower() for skill in profile.get("skills", [])}
    required = {str(skill).lower() for skill in job.get("required_skills", [])}
    if required:
        matched = user_skills & required
        skill_score = 0.4 * (len(matched) / len(required))
    else:
        skill_score = 0.0
    breakdown["skill"] = round(skill_score, 3)
    score += skill_score

    exp_y = profile.get("experience_y", profile.get("experience_years", 0))
    career_score = 0.3 if _career_matches(exp_y, job.get("career_required", "")) else 0.0
    breakdown["career"] = career_score
    score += career_score

    region_score = 0.0
    if profile.get("region") and job.get("location"):
        if profile["region"] in job["location"]:
            region_score = 0.2
        elif str(profile["region"]).split()[0] in job["location"]:
            region_score = 0.1
    breakdown["region"] = region_score
    score += region_score

    days = max(job.get("days_remaining", 999), 1)
    urgency = round(0.1 * (1.0 / days), 3)
    breakdown["urgency"] = urgency
    score += urgency

    if job.get("is_strong_sme"):
        breakdown["sme_bonus"] = 0.05
        score += 0.05

    return min(round(score, 3), 1.0), breakdown


def _career_matches(exp_y: Any, career_required: str) -> bool:
    if not career_required:
        return True
    if "신입" in career_required and int(exp_y or 0) == 0:
        return True
    if "경력" in career_required and int(exp_y or 0) > 0:
        return True
    if "무관" in career_required:
        return True
    return False


def _days_until(date_str: str) -> int:
    try:
        target = date.fromisoformat(date_str)
        return (target - date.today()).days
    except Exception:
        return 999


def _to_int(value: Any) -> int:
    try:
        return int(str(value).replace(",", ""))
    except Exception:
        return 0
