from __future__ import annotations

from typing import Any


def format_policies_to_text(result: dict[str, Any]) -> str:
    items = result.get("items", [])
    if not items:
        return "(정책 결과 없음)"
    lines = []
    for index, item in enumerate(items, 1):
        lines.append(
            f"{index}. {item.get('title', '')}\n"
            f"   - 마감: {item.get('deadline', '')}\n"
            f"   - 점수: {item.get('score', '')}\n"
            f"   - 출처: {item.get('link', '')}"
        )
    return "\n".join(lines)


def format_jobs_to_text(result: dict[str, Any]) -> str:
    items = result.get("items", [])
    if not items:
        return "(채용 결과 없음)"
    lines = []
    for index, item in enumerate(items, 1):
        lines.append(
            f"{index}. {item.get('company', '')} - {item.get('title', '')}\n"
            f"   - 지역: {item.get('location', '')}\n"
            f"   - 마감: {item.get('deadline', '')}\n"
            f"   - 적합도: {item.get('fit_score', '')}\n"
            f"   - 공고: {item.get('url', '')}"
        )
    return "\n".join(lines)


def format_resume_to_text(result: dict[str, Any]) -> str:
    items = result.get("items", [])
    if not items:
        return "(이력서/회사 컨텍스트 결과 없음)"
    lines = []
    for index, item in enumerate(items, 1):
        lines.append(
            f"{index}. {item.get('company', '')}\n"
            f"   - 직무: {item.get('target_role', '')}\n"
            f"   - 강조 키워드: {', '.join(_stringify_values(item.get('emphasize_keywords', [])))}\n"
            f"   - 매칭 포인트: {', '.join(_stringify_values(item.get('matching_points', [])))}"
        )
    return "\n".join(lines)


def format_calendar_to_text(result: dict[str, Any]) -> str:
    items = result.get("items", [])
    if not items:
        return "(일정 결과 없음)"
    lines = []
    for index, item in enumerate(items, 1):
        lines.append(
            f"{index}. {item.get('title', '')}\n"
            f"   - 날짜: {item.get('deadline', '')}\n"
            f"   - D-day: {item.get('days_remaining', '')}"
        )
    return "\n".join(lines)


def _stringify_values(values: Any) -> list[str]:
    if not isinstance(values, list):
        return [str(values)] if values else []
    converted: list[str] = []
    for value in values:
        if isinstance(value, dict):
            if "keyword" in value:
                converted.append(str(value.get("keyword")))
            elif "user_skill" in value and "company_keyword" in value:
                converted.append(f"{value.get('user_skill')} ↔ {value.get('company_keyword')}")
            else:
                converted.append(", ".join(f"{k}={v}" for k, v in value.items()))
        else:
            converted.append(str(value))
    return [value for value in converted if value]
