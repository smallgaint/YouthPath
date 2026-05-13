from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.documents import Document

from core.rag import index_documents


HIGHLIGHT_RE = re.compile(r'<span class="highlight">(.*?)</span>', re.DOTALL)
HTML_TAG_RE = re.compile(r"<[^>]+>")
EMPTY_VALUES = {"", "-", "0", "없음", "해당없음", "제한없음"}

RAW_TEXT_FIELDS: list[tuple[str, str]] = [
    ("PLCY_EXPLN_CN", "정책 설명"),
    ("PLCY_SPRT_CN", "지원 내용"),
    ("ADD_APLY_QLFC_CND_CN", "자격 조건 상세"),
    ("PLCY_APLY_MTHD_CN", "신청 방법"),
    ("SRNG_MTHD_CN", "심사 방법"),
    ("SBMSN_DCMNT_CN", "제출 서류"),
    ("PTCP_PRP_TRGT_CN", "지원 제외 대상"),
    ("ETC_MTTR_CN", "기타 사항"),
    ("EARN_ETC_CN", "소득 조건 상세"),
]

RAW_LABEL_FIELDS: list[tuple[str, str]] = [
    ("PLCY_KYWD_NM", "키워드"),
    ("BIZ_PRD_ETC_CN", "사업 기간"),
    ("MRG_STTS_NM", "결혼 상태"),
    ("QLFC_ACBG_NM", "학력 조건"),
    ("EMPM_STTS_NM", "취업 상태"),
    ("MJR_CND_NM", "전공 조건"),
    ("SPCL_FLD_NM", "특별 분야"),
]


def load_policy_files(data_dir: str = "data/policies") -> list[dict[str, Any]]:
    policies = []
    for path in sorted(Path(data_dir).glob("*.json")):
        policies.append(json.loads(path.read_text(encoding="utf-8")))
    return policies


def build_documents(policies: list[dict[str, Any]], chunk_size: int = 1000, overlap: int = 100) -> list[Document]:
    documents: list[Document] = []
    for policy in policies:
        text = _policy_text(policy)
        if not text:
            continue
        chunks = _chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        policy_id = str(policy.get("policy_id") or policy.get("title") or "")
        raw = policy.get("raw") or {}
        source_url = _clean_text(
            raw.get("REF_URL_ADDR1") or raw.get("APLY_URL_ADDR") or policy.get("link") or ""
        )
        for idx, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "chunk_id": f"{policy_id}:api_raw:{idx}",
                        "policy_id": policy_id,
                        "title": _clean_text(policy.get("title") or ""),
                        "region": _clean_text(policy.get("region") or ""),
                        "min_age": policy.get("min_age") if policy.get("min_age") is not None else -1,
                        "max_age": policy.get("max_age") if policy.get("max_age") is not None else -1,
                        "deadline": _clean_text(policy.get("deadline") or ""),
                        "category": _clean_text(policy.get("category") or ""),
                        "source": "api_raw",
                        "source_priority": 3,
                        "source_url": source_url,
                    },
                )
            )
    return documents


def _policy_text(policy: dict[str, Any]) -> str:
    raw = policy.get("raw") or {}
    header_lines = [
        ("정책명", policy.get("title")),
        ("분야", policy.get("category")),
        ("지역", policy.get("region")),
        ("지원 대상 나이", _format_age(policy.get("min_age"), policy.get("max_age"))),
        ("소득 요약", policy.get("income")),
        ("신청 기간", policy.get("deadline")),
    ]
    for raw_field, label in RAW_LABEL_FIELDS:
        header_lines.append((label, raw.get(raw_field)))

    header = "\n".join(
        f"{label}: {_clean_text(value)}"
        for label, value in header_lines
        if _is_meaningful(value)
    )

    body_sections = []
    for raw_field, label in RAW_TEXT_FIELDS:
        cleaned = _clean_text(raw.get(raw_field))
        if _is_meaningful(cleaned):
            body_sections.append(f"[{label}]\n{cleaned}")

    if not body_sections:
        legacy_description = _clean_text(policy.get("description"))
        legacy_detail = _clean_text(policy.get("detail"))
        if _is_meaningful(legacy_description):
            body_sections.append(f"[정책 설명]\n{legacy_description}")
        if _is_meaningful(legacy_detail):
            body_sections.append(f"[신청 방법]\n{legacy_detail}")

    parts = [header] + body_sections
    return "\n\n".join(part for part in parts if part)


def _format_age(min_age: Any, max_age: Any) -> str:
    if min_age in (None, -1, "") and max_age in (None, -1, ""):
        return ""
    return f"{min_age}~{max_age}"


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = HIGHLIGHT_RE.sub(r"\1", text)
    text = HTML_TAG_RE.sub("", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_meaningful(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    if text in EMPTY_VALUES:
        return False
    return True


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/policies")
    parser.add_argument("--collection", default="policies")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=100)
    args = parser.parse_args()

    policies = load_policy_files(args.data_dir)
    docs = build_documents(policies, chunk_size=args.chunk_size, overlap=args.overlap)
    index_documents(args.collection, docs)
    print(json.dumps({"policies": len(policies), "chunks": len(docs)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
