from __future__ import annotations

from datetime import date
from typing import Any

from Router.job_service import run_job_agent as run_job_agent_service
from Router.resume_service import run_resume_agent as run_resume_agent_service
from Router.schemas import AgentResult


def run_policy_agent(profile: dict[str, Any], query: str) -> dict[str, Any]:
    try:
        from A.services.policy_service import build_policy_response

        return build_policy_response(profile, query)
    except Exception as exc:  # noqa: BLE001
        return AgentResult(
            agent_name="policy",
            items=[],
            sources=[],
            metadata={"partial": True, "query": query},
            error=f"Policy Agent failed: {exc}",
        ).to_dict()


def run_job_agent(profile: dict[str, Any], query: str) -> dict[str, Any]:
    try:
        return run_job_agent_service(profile, query)
    except Exception as exc:  # noqa: BLE001
        return AgentResult(
            agent_name="job",
            items=[],
            sources=[],
            metadata={"partial": True, "query": query},
            error=f"Job Agent failed: {exc}",
        ).to_dict()


def run_resume_agent(profile: dict[str, Any], query: str) -> dict[str, Any]:
    try:
        return run_resume_agent_service(profile, query)
    except Exception as exc:  # noqa: BLE001
        return AgentResult(
            agent_name="resume",
            items=[],
            sources=[],
            metadata={"partial": True, "query": query},
            error=f"Resume Agent failed: {exc}",
        ).to_dict()


def run_calendar_agent(policy_result: dict[str, Any], job_result: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for item in policy_result.get("items", []):
        event = _deadline_event(item, source="policy", title_suffix="정책 마감")
        if event:
            items.append(event)
    for item in job_result.get("items", []):
        event = _deadline_event(item, source="job", title_suffix="채용 마감")
        if event:
            items.append(event)
    items.sort(key=lambda item: (item.get("deadline") or "9999-12-31", item.get("title") or ""))
    return AgentResult(
        agent_name="calendar",
        items=items,
        sources=["router:policy-deadlines", "router:job-deadlines"],
        metadata={"partial": False, "event_count": len(items)},
        error=None,
    ).to_dict()


def _deadline_event(item: dict[str, Any], *, source: str, title_suffix: str) -> dict[str, Any] | None:
    deadline = item.get("deadline")
    if not deadline:
        return None
    title = item.get("title") or item.get("company") or "마감 일정"
    # 로그인 없이 열 수 있는 링크 우선: 정책 신청(apply) URL이면 검색 폴백으로 대체
    link = item.get("link") or item.get("url") or ""
    if item.get("link_kind") == "apply" and item.get("search_url"):
        link = item.get("search_url")
    event = {
        "title": f"{title} {title_suffix}",
        "deadline": deadline,
        "type": source,
        "source": source,
        "link": link,
        "days_remaining": item.get("days_remaining"),
    }
    if event["days_remaining"] is None:
        event["days_remaining"] = _days_until(str(deadline))
    return event


def _days_until(deadline: str) -> int | None:
    try:
        return (date.fromisoformat(deadline[:10]) - date.today()).days
    except Exception:
        return None
