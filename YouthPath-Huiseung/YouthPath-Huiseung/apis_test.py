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

# Set this in .env after copying the request URL from data.go.kr.
# Example:
# PUBLIC_RECRUIT_API_URL="https://apis.data.go.kr/1051000/recruitment"
API_URL_ENV = "PUBLIC_RECRUIT_API_URL"
SERVICE_KEY_ENVS = ("PUBLIC_RECRUIT_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY", "SERVICE_KEY")
DEFAULT_API_URL = ""


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


def service_key() -> str:
    for name in SERVICE_KEY_ENVS:
        if env(name):
            return env(name)
    return ""


def api_url() -> str:
    url = env(API_URL_ENV, DEFAULT_API_URL).rstrip("/")
    if url.endswith("/1051000/recruitment"):
        return f"{url}/list"
    return url


def redact(value: str) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def redact_url_key(url: str, key: str) -> str:
    if not key:
        return url
    return url.replace(key, redact(key))


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def add_if_present(params: dict[str, Any], name: str, value: Any) -> None:
    if value not in (None, ""):
        params[name] = value


def build_params(args: argparse.Namespace, key: str) -> dict[str, Any]:
    params: dict[str, Any] = {
        "serviceKey": key,
        "numOfRows": args.num_of_rows,
        "pageNo": args.page_no,
        "resultType": args.result_type,
    }

    optional_values = {
        "acbgCondLst": args.acbg_cond_lst,
        "hireTypeLst": args.hire_type_lst,
        "instClsf": args.inst_clsf,
        "instType": args.inst_type,
        "ncsCdLst": args.ncs_cd_lst,
        "ongoingYn": args.ongoing_yn,
        "pbancBgngYmd": args.pbanc_bgng_ymd,
        "pbancEndYmd": args.pbanc_end_ymd,
        "pblntInstCd": args.pblnt_inst_cd,
        "recrutPbancTtl": args.recrut_pbanc_ttl,
        "recrutSe": args.recrut_se,
        "replmprYn": args.replmpr_yn,
        "workRgnLst": args.work_rgn_lst,
    }
    for name, value in optional_values.items():
        add_if_present(params, name, value)

    for raw_pair in args.param:
        if "=" not in raw_pair:
            raise SystemExit(f"--param must be KEY=VALUE, got: {raw_pair}")
        name, value = raw_pair.split("=", 1)
        params[name] = value

    return params


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


def unwrap_item(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict) and isinstance(value.get("item"), dict):
        return value["item"]
    if isinstance(value, dict):
        return value
    return None


def find_items(payload: Any) -> list[dict[str, Any]]:
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
            rows.extend(find_items(value))
        return rows

    if isinstance(payload, list):
        rows: list[dict[str, Any]] = []
        for entry in payload:
            item = unwrap_item(entry)
            if item is not None:
                rows.append(item)
            else:
                rows.extend(find_items(entry))
        return rows

    return []


def response_summary(payload: Any, rows: list[dict[str, Any]], fmt: str) -> dict[str, Any]:
    if isinstance(payload, dict):
        return {
            "format": fmt,
            "resultCode": payload.get("resultCode"),
            "resultMsg": payload.get("resultMsg"),
            "totalCount": payload.get("totalCount"),
            "item_count": len(rows),
            "top_level_keys": list(payload.keys()),
        }
    return {"format": fmt, "item_count": len(rows)}


def parse_response(body: str, content_type: str) -> tuple[Any, list[dict[str, Any]], dict[str, Any]]:
    stripped = body.strip()
    looks_json = "json" in content_type.lower() or stripped.startswith(("{", "["))
    if looks_json:
        payload = json.loads(stripped)
        rows = find_items(payload)
        return payload, rows, response_summary(payload, rows, "JSON")

    root = ET.fromstring(stripped)
    payload = xml_to_dict(root)
    rows = find_items(payload)
    return payload, rows, response_summary(payload, rows, "XML")


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


def value_of(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value in (None, ""):
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def normalize_public_recruit(row: dict[str, Any]) -> dict[str, Any]:
    deadline = value_of(row, "pbancEndYmd")
    recruit_id = value_of(row, "recrutPblntSn")
    return {
        "wantedAuthNo": recruit_id,
        "title": value_of(row, "recrutPbancTtl"),
        "company": value_of(row, "instNm"),
        "company_bizno": "",
        "is_strong_sme": False,
        "location": value_of(row, "workRgnNmLst"),
        "region_code": value_of(row, "workRgnLst"),
        "job_code": value_of(row, "ncsCdLst"),
        "job_name": value_of(row, "ncsCdNmLst"),
        "deadline": deadline,
        "days_remaining": days_until(deadline),
        "posted_at": value_of(row, "pbancBgngYmd"),
        "career_required": value_of(row, "recrutSeNm"),
        "education_required": value_of(row, "acbgCondNmLst"),
        "hire_type": value_of(row, "hireTypeNmLst"),
        "recruit_count": to_int(row.get("recrutNope")),
        "ongoing": value_of(row, "ongoingYn"),
        "replacement": value_of(row, "replmprYn"),
        "qualification": value_of(row, "aplyQlfcCn"),
        "preference": value_of(row, "prefCn") or value_of(row, "prefCondCn"),
        "screening": value_of(row, "scrnprcdrMthdExpln"),
        "files": row.get("files", []),
        "steps": row.get("steps", []),
        "source": "public_recruit",
        "url": value_of(row, "srcUrl"),
    }


def run_request(args: argparse.Namespace) -> None:
    key = service_key() or ("DUMMY_SERVICE_KEY" if args.dry_run else "")
    if not key:
        raise SystemExit(
            "Missing service key. Add PUBLIC_RECRUIT_SERVICE_KEY, DATA_GO_KR_SERVICE_KEY, "
            "or SERVICE_KEY to the project-root .env."
        )

    url = args.url or api_url() or ("https://apis.data.go.kr/YOUR_API_PATH" if args.dry_run else "")
    if not url:
        raise SystemExit(
            "Missing API URL. Add PUBLIC_RECRUIT_API_URL to .env or pass --url with the data.go.kr endpoint."
        )

    timeout = float(env("PUBLIC_RECRUIT_TIMEOUT", env("WORKNET_TIMEOUT", "10")))
    params = build_params(args, key)
    safe_params = dict(params)
    safe_params["serviceKey"] = redact(key)

    print("[request]")
    print_json({"url": url, "params": safe_params})

    if args.dry_run:
        print("[dry-run] Request was not sent.")
        return

    response = requests.get(url, params=params, timeout=timeout)
    print(f"[response] status={response.status_code}")
    print(f"[response] content-type={response.headers.get('Content-Type', '')}")
    print(f"[response] final-url={redact_url_key(response.url, key)}")

    body = response.text.strip()
    if args.save_raw:
        raw_path = Path(args.save_raw)
        raw_path.write_text(body, encoding="utf-8")
        print(f"[raw] saved to {raw_path}")

    if not response.ok:
        print("[error-body]")
        print(body[:2000] if body else "<empty>")
        raise SystemExit(f"HTTP {response.status_code}: API request failed.")

    try:
        payload, rows, summary = parse_response(body, response.headers.get("Content-Type", ""))
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
        item = normalize_public_recruit(row)
        item["no"] = idx
        print_json(item)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Public Data Portal recruit announcement API smoke test."
    )
    parser.add_argument("--url", default="", help=f"API endpoint. Overrides {API_URL_ENV}.")
    parser.add_argument("--num-of-rows", type=int, default=10)
    parser.add_argument("--page-no", type=int, default=1)
    parser.add_argument("--result-type", default="json", choices=["json", "xml"])
    parser.add_argument("--preview", type=int, default=5)
    parser.add_argument("--raw", action="store_true", help="Print the full parsed API response.")
    parser.add_argument("--dry-run", action="store_true", help="Print request details without calling the API.")
    parser.add_argument("--save-raw", default="", help="Save raw response body to this path.")
    parser.add_argument("--param", action="append", default=[], help="Override/add one request parameter as KEY=VALUE.")

    parser.add_argument("--acbg-cond-lst", default="", help="학력조건목록, comma-separated.")
    parser.add_argument("--hire-type-lst", default="", help="고용유형목록, comma-separated.")
    parser.add_argument("--inst-clsf", default="", help="기관분류.")
    parser.add_argument("--inst-type", default="", help="기관유형.")
    parser.add_argument("--ncs-cd-lst", default="", help="NCS코드목록, comma-separated.")
    parser.add_argument("--ongoing-yn", default="Y", choices=["", "Y", "N"], help="진행여부.")
    parser.add_argument("--pbanc-bgng-ymd", default="", help="채용공시 시작일 조회시작일, YYYY-MM-DD.")
    parser.add_argument("--pbanc-end-ymd", default="", help="채용공시 시작일 조회종료일, YYYY-MM-DD.")
    parser.add_argument("--pblnt-inst-cd", default="", help="기관코드.")
    parser.add_argument("--recrut-pbanc-ttl", default="", help="공시제목 포함 검색어.")
    parser.add_argument("--recrut-se", default="", help="채용구분.")
    parser.add_argument("--replmpr-yn", default="", choices=["", "Y", "N"], help="대체인력여부.")
    parser.add_argument("--work-rgn-lst", default="", help="근무지역목록, comma-separated.")
    return parser.parse_args()


def main() -> None:
    configure_output_encoding()
    loaded_env = load_env_file()
    args = parse_args()

    print("[env]")
    print_json(
        {
            "loaded_env": str(loaded_env) if loaded_env else None,
            API_URL_ENV: env(API_URL_ENV),
            "service_key_envs": {name: redact(env(name)) for name in SERVICE_KEY_ENVS},
            "PUBLIC_RECRUIT_TIMEOUT": env("PUBLIC_RECRUIT_TIMEOUT", env("WORKNET_TIMEOUT", "10")),
        }
    )

    run_request(args)


if __name__ == "__main__":
    main()
