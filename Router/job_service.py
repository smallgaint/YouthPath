from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from Router.schemas import AgentResult


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_JOB_AGENT_PATH = (
    PROJECT_ROOT
    / "YouthPath-Huiseung"
    / "YouthPath-Huiseung"
    / "YouthPath_JobAgent_apis.py"
)

_PUBLIC_JOB_MODULE: Any | None = None
_PUBLIC_JOB_AGENT: Any | None = None


def run_job_agent(profile: dict[str, Any], query: str) -> dict[str, Any]:
    """Run the Job Agent backed by the public recruitment API."""
    try:
        agent = _get_public_job_agent()
        result = agent.search(query=query, profile=profile)
        metadata = dict(result.get("metadata") or {})
        metadata.update(
            {
                "backend": "public_recruit_api",
                "query": query,
                "agent_file": str(PUBLIC_JOB_AGENT_PATH),
            }
        )
        result["metadata"] = metadata
        return result
    except Exception as exc:  # noqa: BLE001
        return AgentResult(
            agent_name="job",
            items=[],
            sources=["public_data:1051000/recruitment/list"],
            metadata={
                "partial": True,
                "backend": "public_recruit_api",
                "query": query,
                "agent_file": str(PUBLIC_JOB_AGENT_PATH),
            },
            error=f"Public Recruit Job Agent failed: {exc}",
        ).to_dict()


def _get_public_job_agent() -> Any:
    global _PUBLIC_JOB_AGENT
    if _PUBLIC_JOB_AGENT is None:
        module = _load_public_job_module()
        fetcher = module.PublicRecruitFetcher()
        _PUBLIC_JOB_AGENT = module.JobAgent(fetcher)
    return _PUBLIC_JOB_AGENT


def _load_public_job_module() -> Any:
    global _PUBLIC_JOB_MODULE
    if _PUBLIC_JOB_MODULE is not None:
        return _PUBLIC_JOB_MODULE

    if not PUBLIC_JOB_AGENT_PATH.exists():
        raise FileNotFoundError(f"Job Agent file not found: {PUBLIC_JOB_AGENT_PATH}")

    spec = importlib.util.spec_from_file_location(
        "youthpath_public_job_agent",
        PUBLIC_JOB_AGENT_PATH,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load Job Agent module from {PUBLIC_JOB_AGENT_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _PUBLIC_JOB_MODULE = module
    return module
