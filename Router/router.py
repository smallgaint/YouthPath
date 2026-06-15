from __future__ import annotations

import json
import re
import time
from dataclasses import asdict
from typing import Any

from Router.agents import (
    run_calendar_agent,
    run_job_agent,
    run_policy_agent,
    run_resume_agent,
)
from Router.formatters import (
    format_calendar_to_text,
    format_jobs_to_text,
    format_policies_to_text,
    format_resume_to_text,
)
from Router.llm_provider import LLMProvider, get_llm_provider
from Router.schemas import RouterRequest, RouterState


class YouthPathRouter:
    def __init__(self, llm_provider: LLMProvider | None = None):
        self.llm_provider = llm_provider or get_llm_provider()

    def invoke(self, request: RouterRequest | dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        router_request = self._coerce_request(request)
        state = RouterState(
            query=router_request.query,
            profile=router_request.profile,
            user_id=router_request.user_id,
        )

        classification_prompt = self._build_classification_prompt(state)
        classification_raw = self.llm_provider.invoke(
            classification_prompt,
            purpose="classification",
            temperature=0.0,
            max_tokens=300,
        )
        state.classification = self._parse_classification(classification_raw)

        wanted_agents = self._normalize_agents(state.classification.get("agents", []))

        policy_result = {}
        job_result = {}
        resume_result = {}
        calendar_result = {}

        if not wanted_agents:
            state.final_answer = "질문이 너무 포괄적이거나 명확하지 않습니다. 청년 정책, 채용 공고, 자소서 작성 가이드, 마감 일정 중 어떤 도움이 필요하신지 조금 더 구체적으로 질문해 주세요."
        else:
            if "policy" in wanted_agents:
                policy_result = run_policy_agent(state.profile, state.query)
                state.agents["policy"] = policy_result
            if "job" in wanted_agents:
                job_result = run_job_agent(state.profile, state.query)
                state.agents["job"] = job_result
            if "resume" in wanted_agents:
                resume_result = run_resume_agent(state.profile, state.query)
                state.agents["resume"] = resume_result
            # 분류기가 calendar를 고르지 않아도, 정책/채용에 마감일이 있으면 항상 병합한다.
            if (
                "calendar" in wanted_agents
                or policy_result.get("items")
                or job_result.get("items")
            ):
                calendar_result = run_calendar_agent(policy_result, job_result)
                state.agents["calendar"] = calendar_result

            state.formatted_context = {
                "policy": format_policies_to_text(policy_result),
                "job": format_jobs_to_text(job_result),
                "resume": format_resume_to_text(resume_result),
                "calendar": format_calendar_to_text(calendar_result),
            }

            final_prompt = self._build_final_prompt(state)
            state.final_answer = self.llm_provider.invoke(
                final_prompt,
                purpose="final",
                temperature=0.4,
                max_tokens=1200,
            )
        state.metadata = {
            "classification": state.classification,
            "agents_called": list(state.agents.keys()),
            "llm_provider": self.llm_provider.__class__.__name__,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "agent_errors": {
                name: result.get("error")
                for name, result in state.agents.items()
                if result.get("error")
            },
        }

        return {
            "answer": state.final_answer,
            "policy": policy_result.get("items", []),
            "job": job_result.get("items", []),
            "resume": resume_result.get("items", []),
            "calendar": calendar_result.get("items", []),
            "metadata": state.metadata,
            "error": state.error,
        }

    def _coerce_request(self, request: RouterRequest | dict[str, Any]) -> RouterRequest:
        if isinstance(request, RouterRequest):
            return request
        return RouterRequest(
            query=str(request.get("query", "")),
            profile=dict(request.get("profile", {})),
            user_id=request.get("user_id"),
        )

    def _build_classification_prompt(self, state: RouterState) -> str:
        profile = state.profile
        profile_summary = ", ".join(
            part for part in [
                f"{profile.get('age')}세" if profile.get("age") is not None else "",
                profile.get("region", ""),
                profile.get("target_role", ""),
                profile.get("target_company", ""),
            ]
            if part
        )
        return (
            "사용자 질의를 분석하여 호출할 에이전트를 모두 선택하세요.\n\n"
            "에이전트:\n"
            "- policy: 청년 정책, 지원금, 복지\n"
            "- job: 채용공고, 직무, 회사 추천\n"
            "- resume: 기업 컨텍스트와 이력서/자소서 보조\n"
            "- calendar: 마감일, 일정\n\n"
            "JSON 형식: {\"agents\": [...], \"reasoning\": \"...\"}\n\n"
            f"[사용자 프로필 요약]\n{profile_summary}\n\n"
            f"[사용자 질의]\n{state.query}"
        )

    def _build_final_prompt(self, state: RouterState) -> str:
        return (
            "당신은 청년 사회진입 어시스턴트입니다.\n"
            "아래 전문 에이전트 결과를 바탕으로 자연스러운 한국어 답변을 작성하세요.\n\n"
            f"[사용자 질의]\n{state.query}\n\n"
            f"[사용자 프로필]\n{json.dumps(state.profile, ensure_ascii=False)}\n\n"
            f"[정책 결과]\n{state.formatted_context.get('policy', '(정책 결과 없음)')}\n\n"
            f"[채용 결과]\n{state.formatted_context.get('job', '(채용 결과 없음)')}\n\n"
            f"[이력서 결과]\n{state.formatted_context.get('resume', '(이력서 결과 없음)')}\n\n"
            f"[일정 결과]\n{state.formatted_context.get('calendar', '(일정 결과 없음)')}\n\n"
            "답변 작성 규칙:\n"
            "1. 친근하지만 전문적인 어조\n"
            "2. 정책/채용/일정 결과를 구분해서 설명\n"
            "3. 불확실한 내용은 추측하지 말고 '확인 필요'로 표시\n"
            "4. 에이전트 결과가 '없음'인 항목에 대해서는 절대 임의로 지어내어 답변하지 말 것\n"
        )

    @staticmethod
    def _parse_classification(raw_text: str) -> dict[str, Any]:
        try:
            # LLM이 마크다운(```json)이나 불필요한 텍스트를 붙여도 중괄호 내부만 추출
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
        except json.JSONDecodeError:
            pass
        return {"agents": [], "reasoning": "fallback classification"}

    @staticmethod
    def _normalize_agents(raw_agents: Any) -> list[str]:
        valid = {"policy", "job", "resume", "calendar"}
        if isinstance(raw_agents, str):
            raw_agents = [raw_agents]
        if not isinstance(raw_agents, list):
            return []

        agents: list[str] = []
        for agent in raw_agents:
            agent_name = str(agent).strip().lower()
            if agent_name in valid and agent_name not in agents:
                agents.append(agent_name)
        return agents
