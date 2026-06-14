from __future__ import annotations

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime
import importlib.util
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATHS = [Path.cwd() / ".env", PROJECT_ROOT / ".env"]

API_URL_ENV = "PUBLIC_RECRUIT_API_URL"
SERVICE_KEY_ENVS = ("PUBLIC_RECRUIT_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY", "SERVICE_KEY")
DEFAULT_API_URL = "https://apis.data.go.kr/1051000/recruitment/list"


CODE_MAPPING_PATH = Path(__file__).with_name("public_recruit_code_mappings.py")


def load_code_mappings() -> Any:
    spec = importlib.util.spec_from_file_location("public_recruit_code_mappings", CODE_MAPPING_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load public recruit code mappings from {CODE_MAPPING_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CODE_MAPPINGS = load_code_mappings()


def configure_output_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def load_env_file() -> Path | None:
    env_path = next((path for path in ENV_PATHS if path.exists()), None)
    if env_path is None:
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
    return env_path


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def public_recruit_service_key() -> str:
    for name in SERVICE_KEY_ENVS:
        if env(name):
            return env(name)
    return ""


def public_recruit_url() -> str:
    url = env(API_URL_ENV, DEFAULT_API_URL).rstrip("/")
    if url.endswith("/1051000/recruitment"):
        return f"{url}/list"
    return url


def redact_secret(text: str, secret: str) -> str:
    if not secret:
        return text
    if len(secret) <= 8:
        masked = "*" * len(secret)
    else:
        masked = f"{secret[:4]}...{secret[-4:]}"
    return text.replace(secret, masked)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def xml_to_dict(element: ET.Element) -> Any:
    children = list(element)
    if not children:
        return (element.text or "").strip()

    grouped: dict[str, Any] = {}
    for child in children:
        value = xml_to_dict(child)
        if child.tag in grouped:
            if not isinstance(grouped[child.tag], list):
                grouped[child.tag] = [grouped[child.tag]]
            grouped[child.tag].append(value)
        else:
            grouped[child.tag] = value
    return grouped


def unwrap_item(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict) and isinstance(value.get("item"), dict):
        return value["item"]
    if isinstance(value, dict):
        return value
    return None


def find_public_recruit_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        result = payload.get("result")
        if result is not None:
            rows = []
            for entry in as_list(result):
                item = unwrap_item(entry)
                if item is not None:
                    rows.append(item)
            return rows

        response = payload.get("response")
        if isinstance(response, dict):
            body = response.get("body")
            if isinstance(body, dict):
                items = body.get("items")
                if isinstance(items, dict):
                    rows = []
                    for entry in as_list(items.get("item")):
                        item = unwrap_item(entry)
                        if item is not None:
                            rows.append(item)
                    return rows

        rows: list[dict[str, Any]] = []
        for value in payload.values():
            rows.extend(find_public_recruit_items(value))
        return rows

    if isinstance(payload, list):
        rows: list[dict[str, Any]] = []
        for entry in payload:
            item = unwrap_item(entry)
            if item is not None:
                rows.append(item)
            else:
                rows.extend(find_public_recruit_items(entry))
        return rows

    return []


def parse_public_recruit_response(body: str, content_type: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    stripped = body.strip()
    if "json" in content_type.lower() or stripped.startswith(("{", "[")):
        payload = json.loads(stripped)
    else:
        payload = xml_to_dict(ET.fromstring(stripped))

    rows = find_public_recruit_items(payload)
    if isinstance(payload, dict):
        metadata = {
            "resultCode": payload.get("resultCode"),
            "resultMsg": payload.get("resultMsg"),
            "totalCount": payload.get("totalCount"),
            "raw_item_count": len(rows),
        }
    else:
        metadata = {"raw_item_count": len(rows)}
    return rows, metadata


def value_of(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value in (None, ""):
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def to_int(value: Any) -> int:
    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0


def days_until(date_str: str) -> int:
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            target = datetime.strptime(date_str, fmt).date()
            return (target - date.today()).days
        except ValueError:
            pass
    return 999


def contains_any(text: str, words: list[str]) -> list[str]:
    haystack = text.lower()
    return [word for word in words if word and word.lower() in haystack]


def lookup_code(value: Any, codes: dict[str, str]) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text in set(codes.values()):
        return text
    if text in codes:
        return codes[text]

    lowered = text.lower()
    for label, code in codes.items():
        label_lowered = label.lower()
        if lowered == label_lowered or lowered in label_lowered or label_lowered in lowered:
            return code
    return None


def lookup_code_list(value: Any, codes: dict[str, str]) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (list, tuple, set)):
        parts = list(value)
    else:
        parts = [part.strip() for part in str(value).split(",")]

    resolved = []
    for part in parts:
        code = lookup_code(part, codes)
        if code and code not in resolved:
            resolved.append(code)
    return ",".join(resolved) if resolved else None


class PublicRecruitFetcher:
    """공공데이터포털 채용공고 API 클라이언트."""

    def __init__(
        self,
        service_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        load_env_file()
        self.service_key = service_key or public_recruit_service_key()
        self.base_url = (base_url or public_recruit_url()).rstrip("/")
        if self.base_url.endswith("/1051000/recruitment"):
            self.base_url = f"{self.base_url}/list"
        self.timeout = timeout if timeout is not None else float(env("PUBLIC_RECRUIT_TIMEOUT", "6"))

        if not self.service_key:
            raise ValueError(
                "PUBLIC_RECRUIT_SERVICE_KEY, DATA_GO_KR_SERVICE_KEY, or SERVICE_KEY is required."
            )
        if not self.base_url:
            raise ValueError("PUBLIC_RECRUIT_API_URL is required.")

        self.region_codes = CODE_MAPPINGS.REGION_CODES
        self.hire_type_codes = CODE_MAPPINGS.HIRE_TYPE_CODES
        self.recruit_type_codes = CODE_MAPPINGS.RECRUIT_TYPE_CODES
        self.ncs_codes = CODE_MAPPINGS.NCS_CODES
        self.education_codes = CODE_MAPPINGS.EDUCATION_CODES
        self.inst_type_codes = CODE_MAPPINGS.INST_TYPE_CODES
        self.inst_clsf_codes = CODE_MAPPINGS.INST_CLSF_CODES

    def lookup_region(self, region_name: str) -> str | None:
        return lookup_code(region_name, self.region_codes)

    def lookup_hire_type(self, hire_type: Any) -> str | None:
        return lookup_code_list(hire_type, self.hire_type_codes)

    def lookup_recruit_type(self, recruit_type: Any) -> str | None:
        return lookup_code(recruit_type, self.recruit_type_codes)

    def lookup_ncs(self, ncs: Any) -> str | None:
        return lookup_code_list(ncs, self.ncs_codes)

    def lookup_education(self, education: Any) -> str | None:
        return lookup_code_list(education, self.education_codes)

    def lookup_inst_type(self, inst_type: Any) -> str | None:
        return lookup_code(inst_type, self.inst_type_codes)

    def lookup_inst_clsf(self, inst_clsf: Any) -> str | None:
        return lookup_code(inst_clsf, self.inst_clsf_codes)

    def search_jobs(self, filters: dict, display: int = 20) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        filters = dict(filters)
        params = {
            "serviceKey": self.service_key,
            "resultType": "json",
            "pageNo": filters.pop("pageNo", 1),
            "numOfRows": display,
            "ongoingYn": filters.pop("ongoingYn", "Y"),
            **filters,
        }

        response = requests.get(self.base_url, params=params, timeout=self.timeout)
        body = response.text.strip()
        if not response.ok:
            raise RuntimeError(f"Public recruit API HTTP {response.status_code}: {body[:500]}")

        rows, metadata = parse_public_recruit_response(body, response.headers.get("Content-Type", ""))
        if metadata.get("resultCode") not in (None, 0, 200, "0", "200"):
            raise RuntimeError(
                f"Public recruit API error {metadata.get('resultCode')}: {metadata.get('resultMsg')}"
            )
        return rows, metadata


class JobAgent:
    """Job Agent using the public recruitment announcement API."""

    def __init__(self, fetcher: PublicRecruitFetcher):
        self.fetcher = fetcher

    def search(self, query: str, profile: dict) -> dict:
        t_start = time.time()
        attempted_filters: list[dict[str, Any]] = []
        api_metadata: dict[str, Any] = {}
        try:
            filters = self._build_filters(query, profile)
            raw_jobs = []
            selected_filters = filters
            fallback_step = 0
            for fallback_step, candidate_filters in enumerate(self._filter_variants(filters), start=1):
                attempted_filters.append(dict(candidate_filters))
                raw_jobs, api_metadata = self.fetcher.search_jobs(
                    candidate_filters,
                    display=profile.get("display", 20),
                )
                if raw_jobs:
                    selected_filters = candidate_filters
                    break
        except Exception as exc:
            message = redact_secret(str(exc), self.fetcher.service_key)
            return self._error_response(
                t_start,
                f"채용공고 API 호출 실패: {message}",
                metadata={"attempted_filters": attempted_filters},
            )

        if not raw_jobs:
            return self._error_response(
                t_start,
                "채용공고 응답 없음 (조건에 맞는 공고 없음)",
                metadata={"attempted_filters": attempted_filters},
            )

        normalized = [self._normalize(row, profile) for row in raw_jobs]
        for job in normalized:
            job["fit_score"], job["fit_breakdown"] = self._compute_fit_score(profile, job)

        normalized.sort(key=lambda job: job["fit_score"], reverse=True)
        top = normalized[: profile.get("limit", 5)]

        return {
            "agent_name": "job",
            "items": top,
            "sources": ["public_data:1051000/recruitment/list"],
            "metadata": {
                "latency_ms": int((time.time() - t_start) * 1000),
                "api_calls": {"채용공고": 1},
                "totalCount": api_metadata.get("totalCount"),
                "raw_item_count": api_metadata.get("raw_item_count"),
                "selected_filters": dict(selected_filters),
                "attempted_filters": attempted_filters,
                "fallback_step": fallback_step,
                "partial": False,
            },
            "error": None,
        }

    @staticmethod
    def _filter_variants(filters: dict[str, Any]) -> list[dict[str, Any]]:
        variants: list[dict[str, Any]] = []

        def add_variant(candidate: dict[str, Any]) -> None:
            if candidate not in variants:
                variants.append(candidate)

        base = dict(filters)
        add_variant(base)

        # Public recruitment data is sparse; broaden the least semantically important filters first.
        for removable in [
            ("acbgCondLst",),
            ("hireTypeLst",),
            ("recrutSe",),
            ("instType",),
            ("instClsf",),
            ("workRgnLst",),
            ("acbgCondLst", "workRgnLst"),
            ("acbgCondLst", "ncsCdLst"),
            ("workRgnLst", "ncsCdLst"),
            ("acbgCondLst", "workRgnLst", "ncsCdLst"),
        ]:
            candidate = dict(base)
            for key in removable:
                candidate.pop(key, None)
            add_variant(candidate)

        return variants

    def _build_filters(self, query: str, profile: dict) -> dict:
        filters: dict[str, Any] = {}

        # Direct code overrides are preferred because public API code definitions are service-specific.
        direct_map = {
            "work_rgn_lst": "workRgnLst",
            "ncs_cd_lst": "ncsCdLst",
            "acbg_cond_lst": "acbgCondLst",
            "hire_type_lst": "hireTypeLst",
            "inst_clsf": "instClsf",
            "inst_type": "instType",
            "pblnt_inst_cd": "pblntInstCd",
            "recrut_se": "recrutSe",
            "replmpr_yn": "replmprYn",
            "pbanc_bgng_ymd": "pbancBgngYmd",
            "pbanc_end_ymd": "pbancEndYmd",
            "page_no": "pageNo",
            "ongoing_yn": "ongoingYn",
        }
        for profile_key, api_key in direct_map.items():
            value = profile.get(profile_key)
            if value not in (None, ""):
                filters[api_key] = value

        region = profile.get("region")
        if region and "workRgnLst" not in filters:
            region_code = self.fetcher.lookup_region(region)
            if region_code:
                filters["workRgnLst"] = region_code

        if "ncsCdLst" not in filters:
            ncs_value = (
                profile.get("ncs")
                or profile.get("ncs_name")
                or profile.get("job_category")
                or profile.get("target_roles")
            )
            if ncs_value:
                ncs_code = self.fetcher.lookup_ncs(ncs_value)
                if ncs_code:
                    filters["ncsCdLst"] = ncs_code

        if "acbgCondLst" not in filters:
            education = profile.get("education") or profile.get("education_name")
            if education:
                education_code = self.fetcher.lookup_education(education)
                if education_code:
                    filters["acbgCondLst"] = education_code

        if "hireTypeLst" not in filters:
            hire_type = profile.get("hire_type") or profile.get("employment_type")
            if hire_type:
                hire_type_code = self.fetcher.lookup_hire_type(hire_type)
                if hire_type_code:
                    filters["hireTypeLst"] = hire_type_code

        if "recrutSe" not in filters:
            recruit_type = profile.get("recruit_type")
            if recruit_type:
                recruit_type_code = self.fetcher.lookup_recruit_type(recruit_type)
                if recruit_type_code:
                    filters["recrutSe"] = recruit_type_code

        if "instType" not in filters:
            inst_type = profile.get("inst_type_name") or profile.get("institution_type")
            if inst_type:
                inst_type_code = self.fetcher.lookup_inst_type(inst_type)
                if inst_type_code:
                    filters["instType"] = inst_type_code

        if "instClsf" not in filters:
            inst_clsf = profile.get("inst_clsf_name") or profile.get("institution_category")
            if inst_clsf:
                inst_clsf_code = self.fetcher.lookup_inst_clsf(inst_clsf)
                if inst_clsf_code:
                    filters["instClsf"] = inst_clsf_code

        # recrutPbancTtl is an exact-ish title contains filter. Natural-language queries
        # or broad job categories are too restrictive, so use it only when explicitly set.
        keyword = profile.get("keyword") or profile.get("recrut_pbanc_ttl") or ""
        if keyword:
            filters["recrutPbancTtl"] = keyword

        filters.setdefault("ongoingYn", "Y")
        return filters

    def _normalize(self, raw: dict, profile: dict) -> dict:
        deadline = value_of(raw, "pbancEndYmd")
        recruit_id = value_of(raw, "recrutPblntSn")
        title = value_of(raw, "recrutPbancTtl")
        qualification = value_of(raw, "aplyQlfcCn")
        preference = value_of(raw, "prefCn") or value_of(raw, "prefCondCn")
        screening = value_of(raw, "scrnprcdrMthdExpln")
        searchable_text = " ".join(
            [
                title,
                value_of(raw, "ncsCdNmLst"),
                qualification,
                preference,
                screening,
            ]
        )
        profile_skills = [str(skill) for skill in profile.get("skills", [])]
        matched_skills = contains_any(searchable_text, profile_skills)

        return {
            "wantedAuthNo": recruit_id,
            "title": title,
            "company": value_of(raw, "instNm"),
            "company_bizno": "",
            "is_strong_sme": False,
            "location": value_of(raw, "workRgnNmLst"),
            "region_code": value_of(raw, "workRgnLst"),
            "job_code": value_of(raw, "ncsCdLst"),
            "job_name": value_of(raw, "ncsCdNmLst"),
            "deadline": deadline,
            "days_remaining": days_until(deadline),
            "posted_at": value_of(raw, "pbancBgngYmd"),
            "career_required": value_of(raw, "recrutSeNm"),
            "education_required": value_of(raw, "acbgCondNmLst"),
            "salary": {
                "type": "",
                "value": 0,
                "unit": "",
            },
            "hire_type": value_of(raw, "hireTypeNmLst"),
            "recruit_count": to_int(raw.get("recrutNope")),
            "ongoing": value_of(raw, "ongoingYn"),
            "replacement": value_of(raw, "replmprYn"),
            "qualification": qualification,
            "preference": preference,
            "screening": screening,
            "required_skills": matched_skills,
            "preferred_skills": contains_any(preference, profile_skills),
            "fit_score": 0.0,
            "fit_breakdown": {},
            "source": "public_recruit",
            "url": value_of(raw, "srcUrl"),
        }

    def _compute_fit_score(self, profile: dict, job: dict) -> tuple[float, dict]:
        breakdown: dict[str, float] = {}
        score = 0.0

        user_skills = {str(skill).lower() for skill in profile.get("skills", [])}
        matched_skills = {str(skill).lower() for skill in job.get("required_skills", [])}
        if user_skills:
            skill_score = 0.4 * (len(user_skills & matched_skills) / len(user_skills))
        else:
            skill_score = 0.0
        breakdown["skill"] = round(skill_score, 3)
        score += skill_score

        career_score = 0.3 if self._career_matches(profile.get("experience_y", 0), job["career_required"]) else 0.0
        breakdown["career"] = career_score
        score += career_score

        region_score = 0.0
        if profile.get("region") and job["location"]:
            if profile["region"] in job["location"]:
                region_score = 0.2
        breakdown["region"] = region_score
        score += region_score

        days = max(job["days_remaining"], 1)
        urgency = round(0.1 * (1.0 / days), 3)
        breakdown["urgency"] = urgency
        score += urgency

        return min(round(score, 3), 1.0), breakdown

    @staticmethod
    def _career_matches(exp_y: int, career_required: str) -> bool:
        if not career_required:
            return True
        if "신입" in career_required and exp_y == 0:
            return True
        if "경력" in career_required and exp_y > 0:
            return True
        if "무관" in career_required:
            return True
        # Public API often returns "신입+경력"; keep it open for mixed postings.
        if "신입+경력" in career_required:
            return True
        return False

    def _error_response(self, t_start: float, message: str, metadata: dict[str, Any] | None = None) -> dict:
        return {
            "agent_name": "job",
            "items": [],
            "sources": ["public_data:1051000/recruitment/list"],
            "metadata": {
                "latency_ms": int((time.time() - t_start) * 1000),
                "partial": False,
                **(metadata or {}),
            },
            "error": {
                "code": "PUBLIC_RECRUIT_UNAVAILABLE",
                "message": message,
            },
        }


def demo() -> None:
    configure_output_encoding()
    load_env_file()
    fetcher = PublicRecruitFetcher()
    agent = JobAgent(fetcher)
    profile = {
        "region": "서울",
        "ncs": "정보통신",
        "skills": ["Python", "SQL", "Tableau", "JavaScript"],
        "experience_y": 0,
        "education": "대졸",
        "display": 3,
        "limit": 3,
    }
    result = agent.search(query="데이터 채용 공고", profile=profile)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    demo()
