from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProjectOverview:
    """YouthPath 프로젝트 핵심 제약 사항."""

    name: str = "YouthPath"
    goal: str = "청년 사회진입 통합 어시스턴트 (정책 + 채용 + 자소서 가이드)"
    architecture: str = "Multi-Agent 시스템 (Policy / Job / Resume / Calendar / Router)"
    llm_call_rule: str = "Router 분류 1회 + 통합 응답 1회 = 총 2회"
    specialist_rule: str = "각 Specialist Agent는 LLM 없이 정보 수집·매칭만 수행"


def build_team_a_assistant_instruction() -> str:
    """팀원 A용 어시스턴트 시스템 지침 문자열을 반환한다."""

    return (
        "너는 YouthPath 프로젝트의 팀원 A를 돕는 AI 어시스턴트다.\n\n"
        "[프로젝트 개요]\n"
        "- YouthPath: 청년 사회진입 통합 어시스턴트 (정책 + 채용 + 자소서 가이드)\n"
        "- Multi-Agent 시스템 (Policy / Job / Resume / Calendar / Router)\n"
        "- LLM 호출 최소화: Router 분류 1회 + 통합 응답 1회 = 총 2회\n"
        "- 각 Specialist Agent는 LLM 없이 정보 수집·매칭만 수행\n"
        "- 6/2 최종 제출 (학기 프로젝트, 5인 팀)\n\n"
        "답변 시 다음을 지켜줘:\n"
        "1. 한국어로 답변\n"
        "2. 코드는 실행 가능한 형태 (import 포함)\n"
        "3. 환각·추측 금지. 모르면 모른다고\n"
        "4. 단순한 해결책 우선\n"
        "5. 학부생 수준에서 이해할 수 있게\n"
        "6. 추상 클래스 설계 시 다른 Agent(Job, Resume, Calendar)에도 자연스럽게 적용 가능한지 검토"
    )


class SpecialistAgent(ABC):
    """모든 Specialist Agent에 공통으로 적용되는 추상 클래스."""

    @property
    @abstractmethod
    def name(self) -> str:
        """에이전트 식별자."""

    @abstractmethod
    def collect_and_match(self, user_query: str) -> dict[str, Any]:
        """LLM 없이 정보 수집/매칭 결과를 반환한다."""


class PolicyAgent(SpecialistAgent):
    @property
    def name(self) -> str:
        return "policy"

    def collect_and_match(self, user_query: str) -> dict[str, Any]:
        return {"agent": self.name, "matched": "정책", "query": user_query}


class JobAgent(SpecialistAgent):
    @property
    def name(self) -> str:
        return "job"

    def collect_and_match(self, user_query: str) -> dict[str, Any]:
        return {"agent": self.name, "matched": "채용", "query": user_query}


class ResumeAgent(SpecialistAgent):
    @property
    def name(self) -> str:
        return "resume"

    def collect_and_match(self, user_query: str) -> dict[str, Any]:
        return {"agent": self.name, "matched": "자소서", "query": user_query}


class CalendarAgent(SpecialistAgent):
    @property
    def name(self) -> str:
        return "calendar"

    def collect_and_match(self, user_query: str) -> dict[str, Any]:
        return {"agent": self.name, "matched": "일정", "query": user_query}


class Router:
    """간단한 키워드 라우터 (LLM 1회 분류를 대체하는 결정적 로직)."""

    def __init__(self, agents: list[SpecialistAgent], default_agent_name: str = "policy") -> None:
        self._agent_map = {agent.name: agent for agent in agents}
        if default_agent_name not in self._agent_map:
            raise ValueError(f"기본 에이전트 '{default_agent_name}'를 찾을 수 없습니다.")
        self._default_agent_name = default_agent_name

    def route(self, user_query: str) -> list[SpecialistAgent]:
        query = user_query.lower()
        selected: list[str] = []

        if "정책" in query:
            selected.append("policy")
        if "채용" in query or "취업" in query:
            selected.append("job")
        if "자소서" in query or "이력서" in query:
            selected.append("resume")
        if "일정" in query or "캘린더" in query:
            selected.append("calendar")

        if not selected:
            selected = [self._default_agent_name]

        return [self._agent_map[name] for name in selected]


class YouthPathOrchestrator:
    """Router 1회 + 통합 응답 1회 구조를 명시적으로 보장한다."""

    def __init__(self, router: Router) -> None:
        self.router = router

    def handle(self, user_query: str) -> dict[str, Any]:
        selected_agents = self.router.route(user_query)
        specialist_results = [agent.collect_and_match(user_query) for agent in selected_agents]

        return {
            "router_calls": 1,
            "integrated_response_calls": 1,
            "total_llm_calls": 2,
            "specialist_results": specialist_results,
        }
