import asyncio
import importlib.util
import json
import sys
from pathlib import Path

from Router.llm_provider import LLMProvider
from Router.router import YouthPathRouter


class ForcedJobResumeProvider(LLMProvider):
    def invoke(self, prompt: str, **kwargs):
        if "JSON 형식" in prompt:
            return json.dumps(
                {
                    "agents": ["job", "resume"],
                    "reasoning": "e2e verification: skip policy path for stable test",
                },
                ensure_ascii=False,
            )
        return "[E2E-OK] Router merged job/resume results successfully."


class ForcedAllProvider(LLMProvider):
    def invoke(self, prompt: str, **kwargs):
        if "JSON 형식" in prompt:
            return json.dumps(
                {
                    "agents": ["policy", "job", "resume", "calendar"],
                    "reasoning": "e2e verification: include policy branch and deadline merge",
                },
                ensure_ascii=False,
            )
        return "[E2E-OK] Router merged policy/job/resume/calendar results successfully."


def _load_jaewon_main():
    root = Path(__file__).resolve().parent
    jaewon_main_path = root / "YouthPath-jaewon" / "YouthPath-jaewon" / "main.py"
    if not jaewon_main_path.exists():
        raise FileNotFoundError(f"Jaewon main.py not found: {jaewon_main_path}")

    module_name = "jaewon_main_e2e"
    spec = importlib.util.spec_from_file_location(module_name, jaewon_main_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create import spec for {jaewon_main_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


async def _run():
    jaewon_main = _load_jaewon_main()

    # Scenario 1: force a deterministic router path for endpoint-level e2e validation.
    jaewon_main.router = YouthPathRouter(llm_provider=ForcedJobResumeProvider())

    request = jaewon_main.AskRequest(
        query="백엔드 신입 취업 준비를 도와줘",
        profile={
            "age": 24,
            "region": "서울",
            "target_role": "백엔드 개발자",
            "target_company": "핀테크",
            "skills": ["python", "fastapi", "sql"],
        },
        user_id="e2e-user-001",
    )

    response = await jaewon_main.ask(request)

    print("=== E2E /ask result: job+resume ===")
    print("answer:", response.get("answer"))
    print("counts:", {
        "policy": len(response.get("policy", [])),
        "job": len(response.get("job", [])),
        "resume": len(response.get("resume", [])),
        "calendar": len(response.get("calendar", [])),
    })
    print("metadata:", response.get("metadata"))
    print("keys:", sorted(response.keys()))

    # Scenario 2: include policy branch and calendar merge.
    jaewon_main.router = YouthPathRouter(llm_provider=ForcedAllProvider())
    policy_request = jaewon_main.AskRequest(
        query="서울 청년 월세 정책이랑 데이터 분석 신입 공고, 자소서 준비까지 한 번에 정리해줘",
        profile={
            "age": 27,
            "region": "서울",
            "income_bracket": 60,
            "target_role": "데이터 분석가",
            "target_company": "네이버",
            "company_identifier": "035420",
            "skills": ["Python", "SQL", "FastAPI"],
            "experience_y": 0,
        },
        user_id="e2e-user-002",
    )
    policy_response = await jaewon_main.ask(policy_request)
    print("=== E2E /ask result: policy+job+resume+calendar ===")
    print("answer:", policy_response.get("answer"))
    print("counts:", {
        "policy": len(policy_response.get("policy", [])),
        "job": len(policy_response.get("job", [])),
        "resume": len(policy_response.get("resume", [])),
        "calendar": len(policy_response.get("calendar", [])),
    })
    print("metadata:", policy_response.get("metadata"))
    print("keys:", sorted(policy_response.keys()))


if __name__ == "__main__":
    asyncio.run(_run())
