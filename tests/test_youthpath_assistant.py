import unittest

from youthpath_assistant import (
    CalendarAgent,
    JobAgent,
    PolicyAgent,
    ResumeAgent,
    Router,
    YouthPathOrchestrator,
    build_team_a_assistant_instruction,
)


class YouthPathAssistantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agents = [PolicyAgent(), JobAgent(), ResumeAgent(), CalendarAgent()]
        self.router = Router(self.agents)
        self.orchestrator = YouthPathOrchestrator(self.router)

    def test_instruction_includes_required_rules(self) -> None:
        instruction = build_team_a_assistant_instruction()
        self.assertIn("1. 한국어로 답변", instruction)
        self.assertIn("2. 코드는 실행 가능한 형태 (import 포함)", instruction)
        self.assertIn("3. 환각·추측 금지. 모르면 모른다고", instruction)
        self.assertIn("4. 단순한 해결책 우선", instruction)
        self.assertIn("5. 학부생 수준에서 이해할 수 있게", instruction)
        self.assertIn(
            "6. 추상 클래스 설계 시 다른 Agent(Job, Resume, Calendar)에도 자연스럽게 적용 가능한지 검토",
            instruction,
        )

    def test_router_and_orchestrator_follow_minimum_call_contract(self) -> None:
        result = self.orchestrator.handle("정책과 자소서, 일정을 같이 보고 싶어요")
        self.assertEqual(result["router_calls"], 1)
        self.assertEqual(result["integrated_response_calls"], 1)
        self.assertEqual(result["total_llm_calls"], 2)

        agent_names = {item["agent"] for item in result["specialist_results"]}
        self.assertSetEqual(agent_names, {"policy", "resume", "calendar"})

    def test_specialist_abstract_design_applies_to_all_agents(self) -> None:
        for agent in self.agents:
            output = agent.collect_and_match("테스트 질의")
            self.assertIn("agent", output)
            self.assertIn("matched", output)
            self.assertIn("query", output)

    def test_router_default_agent_is_configurable(self) -> None:
        router = Router(self.agents, default_agent_name="job")
        result = YouthPathOrchestrator(router).handle("키워드가 없는 질의")
        self.assertEqual(result["specialist_results"][0]["agent"], "job")


if __name__ == "__main__":
    unittest.main()
