from __future__ import annotations

import asyncio
import importlib.util
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from Router.schemas import AgentResult


def run_resume_agent(profile: dict[str, Any], query: str) -> dict[str, Any]:
    t_start = datetime.now()
    live_result, live_error = _try_run_jeonghyun_pipeline(profile)
    if live_result:
        return _normalize_resume_result(
            live_result,
            query=query,
            latency_ms=int((datetime.now() - t_start).total_seconds() * 1000),
            backend="jeonghyun-dart-naver",
        )

    target_company = str(profile.get("target_company", "")).strip()
    target_role = str(profile.get("target_role", "")).strip()
    skills = [str(skill).strip() for skill in profile.get("skills", []) if str(skill).strip()]

    item = {
        "company": target_company or "미지정",
        "company_identifier": str(profile.get("company_identifier", "")),
        "target_role": target_role or "미지정",
        "emphasize_keywords": _derive_emphasize_keywords(skills, target_role),
        "matching_points": _build_matching_points(skills, target_company, target_role),
        "evidence_gaps": _build_evidence_gaps(skills, target_role),
        "story_angles": _build_story_angles(target_company, target_role, skills),
        "dynamic_news": [],
        "static_disclosure_chunks": [],
        "retrieved_chunk_count": 0,
    }

    return AgentResult(
        agent_name="resume",
        items=[item],
        sources=["router:resume-context"],
        metadata={
            "llm_used": False,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "query": query,
            "backend": "fallback-rule",
            "partial": True,
            "latency_ms": int((datetime.now() - t_start).total_seconds() * 1000),
            "note": "Jeonghyun DART/Naver pipeline was attempted first; fallback context was generated locally.",
        },
        error=live_error,
    ).to_dict()


def _try_run_jeonghyun_pipeline(profile: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        module = _load_jeonghyun_app()
        if not hasattr(module, "load_companies_collection") or not hasattr(module, "run_resume_agent"):
            raise RuntimeError("Jeonghyun app module does not expose the expected resume pipeline functions.")
        collection = module.load_companies_collection()
        result = _run_coro_in_thread(module.run_resume_agent(profile=profile, collection=collection))
        if isinstance(result, dict) and not result.get("error"):
            try:
                context_text = module.format_agent_output_to_text(result)
                module.save_resume_agent_context(result, context_text)
            except Exception:
                pass
            return result, None
        if isinstance(result, dict):
            return None, result.get("error") or "Jeonghyun pipeline returned no usable resume result."
        return None, "Jeonghyun pipeline returned an unexpected result."
    except Exception as exc:  # noqa: BLE001
        return None, f"Jeonghyun DART/Naver pipeline unavailable: {exc}"


def _load_jeonghyun_app():
    root = Path(__file__).resolve().parents[1]
    app_path = root / "YouthPath-Jeonghyun" / "YouthPath-Jeonghyun" / "app.py"
    module_name = "youthpath_jeonghyun_resume_app"
    if module_name in sys.modules:
        return sys.modules[module_name]
    if not app_path.exists():
        raise FileNotFoundError(app_path)
    spec = importlib.util.spec_from_file_location(module_name, app_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load import spec for {app_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def _run_coro_in_thread(coro):
    result_box: dict[str, Any] = {}

    def runner() -> None:
        try:
            result_box["result"] = asyncio.run(coro)
        except Exception as exc:  # noqa: BLE001
            result_box["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join(timeout=45)
    if thread.is_alive():
        raise TimeoutError("Resume pipeline timed out after 45 seconds.")
    if "error" in result_box:
        raise result_box["error"]
    return result_box.get("result")


def _normalize_resume_result(
    result: dict[str, Any],
    *,
    query: str,
    latency_ms: int,
    backend: str,
) -> dict[str, Any]:
    if "items" in result:
        items = result.get("items", [])
    else:
        items = [{
            "company": result.get("company"),
            "company_identifier": result.get("company_identifier"),
            "target_role": result.get("target_role", ""),
            "emphasize_keywords": result.get("emphasize_keywords", []),
            "matching_points": result.get("matching_points", []),
            "evidence_gaps": result.get("evidence_gaps", []),
            "story_angles": result.get("story_angles", []),
            "dynamic_news": result.get("dynamic_news", []),
            "static_disclosure_chunks": result.get("static_disclosure_chunks", []),
            "retrieved_chunk_count": result.get("retrieved_chunk_count", 0),
        }]
    metadata = dict(result.get("metadata") or {})
    metadata.update({
        "llm_used": False,
        "backend": backend,
        "partial": False,
        "latency_ms": latency_ms,
        "query": query,
    })
    return AgentResult(
        agent_name="resume",
        items=items,
        sources=list(result.get("sources", ["ChromaDB companies", "DART disclosure chunks", "Naver News API"])),
        metadata=metadata,
        error=result.get("error"),
    ).to_dict()


def _derive_emphasize_keywords(skills: list[str], target_role: str) -> list[str]:
    keywords = list(dict.fromkeys(skills[:5]))
    if target_role and target_role not in keywords:
        keywords.insert(0, target_role)
    return keywords[:5]


def _build_matching_points(skills: list[str], target_company: str, target_role: str) -> list[str]:
    points = []
    if skills:
        points.append(f"보유 스킬: {', '.join(skills[:3])}")
    if target_company:
        points.append(f"지원 기업: {target_company}")
    if target_role:
        points.append(f"희망 직무: {target_role}")
    return points


def _build_evidence_gaps(skills: list[str], target_role: str) -> list[str]:
    gaps: list[str] = []
    if target_role and not skills:
        gaps.append("직무 연관 경험을 구체화할 재료가 부족합니다.")
    elif target_role:
        gaps.append(f"{target_role}와 연결되는 프로젝트/성과를 1~2개 더 보강하면 좋습니다.")
    return gaps


def _build_story_angles(target_company: str, target_role: str, skills: list[str]) -> list[str]:
    return [
        f"{target_company or '희망 기업'}의 사업/서비스와 {target_role or '희망 직무'}를 연결한 지원 동기",
        f"{', '.join(skills[:2]) if skills else '보유 역량'}를 활용한 문제 해결 경험",
        "팀 협업 또는 프로젝트에서의 역할과 성장 포인트",
    ]
