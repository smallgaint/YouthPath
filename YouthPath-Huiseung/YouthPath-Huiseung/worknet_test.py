from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATHS = [Path.cwd() / ".env", PROJECT_ROOT / ".env"]

WORKNET_BASE = "https://www.work24.go.kr/cm/openApi/call"
RECRUIT_PATH = "/wk/callOpenApiSvcInfo210L01.do"
DEFAULT_RECRUIT_URL = WORKNET_BASE + RECRUIT_PATH

# Same fallback mappings used by 딥러닝및응용_YouthPath_JobAgent.py.
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
    "강원": "42",
    "충북": "43",
    "충남": "44",
    "전북": "45",
    "전남": "46",
    "경북": "47",
    "경남": "48",
    "제주": "50",
}
CAREER_CODES = {"신입": "1", "경력": "2", "무관": "3"}
EDU_CODES = {
    "학력무관": "00",
    "고졸이하": "01",
    "전문대졸": "02",
    "대졸": "03",
    "석사": "04",
    "박사": "05",
}
JOB_CODES = {
    "데이터 분석": "2236",
    "데이터 분석가": "2236",
    "데이터분석가": "2236",
    "백엔드 개발": "2231",
    "백엔드 개발자": "2231",
    "프론트엔드 개발": "2232",
    "프론트엔드 개발자": "2232",
    "AI 엔지니어": "2235",
    "머신러닝 엔지니어": "2235",
    "기획자": "1320",
    "서비스 기획자": "1320",
}


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


def worknet_key() -> str:
    return env("WORKNET_RECRUIT_API_KEY") or env("WORKNET_API_KEY")


def recruit_url() -> str:
    if env("WORKNET_RECRUIT_URL"):
        return env("WORKNET_RECRUIT_URL")
    if env("WORKNET_BASE_URL") and env("WORKNET_RECRUIT_PATH"):
        return env("WORKNET_BASE_URL").rstrip("/") + "/" + env("WORKNET_RECRUIT_PATH").lstrip("/")
    return DEFAULT_RECRUIT_URL


def redact(value: str) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def redact_url_key(url: str, api_key: str) -> str:
    if not api_key:
        return url
    return url.replace(api_key, redact(api_key))


def lookup_job(role_name: str) -> str | None:
    if role_name in JOB_CODES:
        return JOB_CODES[role_name]
    for key, value in JOB_CODES.items():
        if role_name in key or key in role_name:
            return value
    return None


def build_agent_filters(args: argparse.Namespace) -> dict[str, str]:
    filters: dict[str, str] = {}

    if args.region_name:
        code = REGION_CODES.get(args.region_name)
        if code:
            filters["regionCd"] = code
    if args.target_role:
        code = lookup_job(args.target_role)
        if code:
            filters["jobCd"] = code
    if args.experience_y is not None:
        filters["empTpCd"] = CAREER_CODES["신입"] if args.experience_y == 0 else CAREER_CODES["경력"]
    if args.education_name:
        filters["eduLvCd"] = EDU_CODES.get(args.education_name, EDU_CODES["학력무관"])

    return filters


def build_request_params(args: argparse.Namespace, api_key: str) -> dict[str, Any]:
    params: dict[str, Any] = {
        "authKey": api_key,
        "returnType": args.return_type,
        "startPage": args.start_page,
        "display": args.display,
    }

    if args.param_style == "agent":
        params.update(build_agent_filters(args))
    else:
        # Older Worknet docs use these names. This mode is handy when comparing with docs.
        optional_values = {
            "callTp": "L",
            "keyword": args.keyword,
            "region": args.region,
            "occupation": args.occupation,
            "career": args.career,
            "education": args.education,
            "salTp": args.sal_tp,
            "minPay": args.min_pay,
            "maxPay": args.max_pay,
            "empTpGb": args.emp_tp_gb,
            "sortOrderBy": args.sort_order_by,
        }
        for key, value in optional_values.items():
            if value not in (None, ""):
                params[key] = value

    # Direct overrides make it easy to test uncertain Work24 parameter names.
    for raw_pair in args.param:
        if "=" not in raw_pair:
            raise SystemExit(f"--param must be KEY=VALUE, got: {raw_pair}")
        key, value = raw_pair.split("=", 1)
        params[key] = value

    return params


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def text_of(parent: ET.Element, tag: str) -> str:
    node = parent.find(tag)
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def first_text(root: ET.Element, *tags: str) -> str:
    for tag in tags:
        value = text_of(root, tag)
        if value:
            return value
        node = root.find(f".//{tag}")
        if node is not None and node.text:
            return node.text.strip()
    return ""


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


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def find_wanted_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        wanted_root = payload.get("wantedRoot")
        if isinstance(wanted_root, dict) and "wanted" in wanted_root:
            return [row for row in as_list(wanted_root.get("wanted")) if isinstance(row, dict)]
        if "wanted" in payload:
            return [row for row in as_list(payload.get("wanted")) if isinstance(row, dict)]

        rows: list[dict[str, Any]] = []
        for value in payload.values():
            rows.extend(find_wanted_rows(value))
        return rows

    if isinstance(payload, list):
        rows: list[dict[str, Any]] = []
        for item in payload:
            rows.extend(find_wanted_rows(item))
        return rows

    return []


def parse_response(body: str, content_type: str) -> tuple[str, Any, list[dict[str, Any]], dict[str, Any]]:
    stripped = body.strip()
    looks_json = "json" in content_type.lower() or stripped.startswith(("{", "["))
    if looks_json:
        payload = json.loads(stripped)
        rows = find_wanted_rows(payload)
        summary = {
            "format": "JSON",
            "wanted_count": len(rows),
            "top_level_keys": list(payload.keys()) if isinstance(payload, dict) else None,
            "error": payload.get("error") if isinstance(payload, dict) else None,
            "message": payload.get("message") if isinstance(payload, dict) else None,
        }
        return "JSON", payload, rows, summary

    root = ET.fromstring(stripped)
    payload = xml_to_dict(root)
    rows = []
    for wanted in root.findall(".//wanted"):
        row = {child.tag: (child.text or "").strip() for child in list(wanted)}
        rows.append(row)

    summary = {
        "format": "XML",
        "root": root.tag,
        "total": first_text(root, "total"),
        "startPage": first_text(root, "startPage"),
        "display": first_text(root, "display"),
        "wanted_count": len(rows),
        "message": first_text(root, "message", "msg"),
        "error": first_text(root, "error", "errMsg", "errorMsg"),
    }
    return "XML", payload, rows, summary


def days_until(date_str: str) -> int:
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            target = datetime.strptime(date_str, fmt).date()
            return (target - date.today()).days
        except ValueError:
            pass
    return 999


def to_int(value: Any) -> int:
    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0


def value_of(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def normalize_like_agent(row: dict[str, Any]) -> dict[str, Any]:
    deadline = value_of(row, "closeDt", "closeDate", "receiptCloseDt")
    wanted_auth_no = value_of(row, "wantedAuthNo", "wantedAuthNo")
    return {
        "wantedAuthNo": wanted_auth_no,
        "title": value_of(row, "title", "wantedTitle"),
        "company": value_of(row, "company", "companyNm"),
        "company_bizno": value_of(row, "bizNo", "busiNo"),
        "location": value_of(row, "region", "basicAddr"),
        "region_code": value_of(row, "regionCd"),
        "job_code": value_of(row, "jobsCd", "jobCd", "occupation"),
        "deadline": deadline,
        "days_remaining": days_until(deadline),
        "posted_at": value_of(row, "regDt", "regDate"),
        "career_required": value_of(row, "career", "careerCond"),
        "education_required": value_of(row, "minEdubg", "education"),
        "salary": {
            "type": value_of(row, "salTpNm", "salaryType"),
            "value": to_int(value_of(row, "sal", "salary")),
            "unit": "만원",
        },
        "source": "worknet",
        "url": value_of(row, "wantedInfoUrl")
        or f"https://www.work.go.kr/empSpt/empSrch/empSrchView.do?wantedAuthNo={wanted_auth_no}",
    }


def run_request(args: argparse.Namespace) -> None:
    api_key = worknet_key()
    if not api_key:
        raise SystemExit(
            "Missing Worknet key. Add WORKNET_API_KEY or WORKNET_RECRUIT_API_KEY to the project-root .env."
        )

    url = recruit_url()
    timeout = float(env("WORKNET_TIMEOUT", "10"))
    params = build_request_params(args, api_key)
    safe_params = dict(params)
    safe_params["authKey"] = redact(api_key)

    print("[agent-flow]")
    print_json(
        {
            "source_file": "딥러닝및응용_YouthPath_JobAgent.py",
            "tested_method": "WorknetFetcher.search_jobs",
            "param_style": args.param_style,
            "agent_profile": {
                "region": args.region_name,
                "target_role": args.target_role,
                "experience_y": args.experience_y,
                "education": args.education_name,
            },
            "agent_filters": build_agent_filters(args),
        }
    )

    print("[request]")
    print_json({"url": url, "params": safe_params})

    if args.dry_run:
        print("[dry-run] Request was not sent.")
        return

    response = requests.get(url, params=params, timeout=timeout)
    print(f"[response] status={response.status_code}")
    print(f"[response] content-type={response.headers.get('Content-Type', '')}")
    print(f"[response] final-url={redact_url_key(response.url, api_key)}")
    response.raise_for_status()

    body = response.text.strip()
    if args.save_raw:
        raw_path = Path(args.save_raw)
        raw_path.write_text(body, encoding="utf-8")
        print(f"[raw] saved to {raw_path}")

    try:
        _, payload, rows, summary = parse_response(body, response.headers.get("Content-Type", ""))
    except (ET.ParseError, json.JSONDecodeError):
        print("[error] Response is neither valid JSON nor valid XML. First 2000 characters:")
        print(body[:2000])
        raise

    print("[summary]")
    print_json(summary)

    if args.raw:
        print("[raw-parsed]")
        print_json(payload)
        return

    print("[preview:agent-normalized]")
    for idx, row in enumerate(rows[: args.preview], start=1):
        item = normalize_like_agent(row)
        item["no"] = idx
        print_json(item)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Work24/Worknet recruit API smoke test mirroring YouthPath JobAgent.search_jobs."
    )
    parser.add_argument("--param-style", choices=["agent", "docs"], default="agent")
    parser.add_argument("--return-type", choices=["JSON", "XML"], default="JSON")
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--display", type=int, default=10)
    parser.add_argument("--preview", type=int, default=5)
    parser.add_argument("--raw", action="store_true", help="Print the full parsed API response.")
    parser.add_argument("--dry-run", action="store_true", help="Print request details without calling Worknet.")
    parser.add_argument("--save-raw", default="", help="Save raw response body to this path.")
    parser.add_argument("--param", action="append", default=[], help="Override/add one request parameter as KEY=VALUE.")

    # JobAgent-style profile inputs.
    parser.add_argument("--region-name", default="서울")
    parser.add_argument("--target-role", default="데이터 분석가")
    parser.add_argument("--experience-y", type=int, default=0)
    parser.add_argument("--education-name", default="대졸")

    # Docs-style parameters kept for comparison against Work24 documentation.
    parser.add_argument("--keyword", default="")
    parser.add_argument("--region", default="", help="Docs-style work region code. Example: Seoul=11.")
    parser.add_argument("--occupation", default="", help="Docs-style occupation code. Multiple codes may use '|'.")
    parser.add_argument("--career", default="")
    parser.add_argument("--education", default="")
    parser.add_argument("--sal-tp", default="")
    parser.add_argument("--min-pay", default="")
    parser.add_argument("--max-pay", default="")
    parser.add_argument("--emp-tp-gb", default="")
    parser.add_argument("--sort-order-by", default="DESC", choices=["DESC", "ASC"])
    return parser.parse_args()


def main() -> None:
    configure_output_encoding()
    loaded_env = load_env_file()
    args = parse_args()

    print("[env]")
    print_json(
        {
            "loaded_env": str(loaded_env) if loaded_env else None,
            "WORKNET_API_KEY": redact(env("WORKNET_API_KEY")),
            "WORKNET_RECRUIT_API_KEY": redact(env("WORKNET_RECRUIT_API_KEY")),
            "WORKNET_RECRUIT_URL": env("WORKNET_RECRUIT_URL", DEFAULT_RECRUIT_URL),
            "WORKNET_TIMEOUT": env("WORKNET_TIMEOUT", "10"),
        }
    )

    run_request(args)


if __name__ == "__main__":
    main()
