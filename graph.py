import asyncio
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END

from state import GraphState
from router import router_node
from formatters import (
    format_policy_result,
    format_job_result,
    format_resume_result,
    format_calendar_result,
)

# ---------------------------------------------------------
# 에이전트 스텁 함수
# 각 팀원이 구현한 async 함수로 교체 예정.
# 예: from agents.policy_agent import run_policy_agent
# ---------------------------------------------------------
async def _stub_policy_agent(query: str, profile: dict) -> Optional[dict]:
    """[TODO] 정책 팀원 구현체로 교체"""
    print("[Policy Agent] 실행 (스텁)")
    return None

async def _stub_job_agent(query: str, profile: dict) -> Optional[dict]:
    """[TODO] 채용 팀원 구현체로 교체"""
    print("[Job Agent] 실행 (스텁)")
    return None

async def _stub_resume_agent(query: str, profile: dict) -> Optional[dict]:
    """[TODO] 자소서 팀원 구현체로 교체"""
    print("[Resume Agent] 실행 (스텁)")
    return None

async def _stub_calendar_agent(query: str, profile: dict) -> Optional[dict]:
    """[TODO] 일정 팀원 구현체로 교체"""
    print("[Calendar Agent] 실행 (스텁)")
    return None

# 에이전트 이름 → (state 키, 실행 함수) 매핑
AGENT_REGISTRY = {
    "policy":   ("policy_result",   _stub_policy_agent),
    "job":      ("job_result",      _stub_job_agent),
    "resume":   ("resume_result",   _stub_resume_agent),
    "calendar": ("calendar_result", _stub_calendar_agent),
}


# ---------------------------------------------------------
# 1. 에이전트 병렬 실행 오케스트레이터 노드
# ---------------------------------------------------------
async def agents_orchestrator_node(state: GraphState) -> Dict[str, Any]:
    """
    라우터 결정에 따라 선택된 에이전트들을 asyncio.gather로 병렬 실행합니다.
    개별 에이전트 오류는 None으로 처리해 통합 LLM이 '(해당 결과 없음)'으로 대응하게 합니다.
    """
    decision = state.get("router_decision", {})
    active_agents = decision.get("agents", [])

    print(f"[Orchestrator] 병렬 실행 대상: {active_agents}")

    query = state.get("query", "")
    profile = state.get("user_profile", {})

    # 선택된 에이전트만 태스크 생성
    keys = []
    coroutines = []
    for agent_name in active_agents:
        if agent_name in AGENT_REGISTRY:
            state_key, fn = AGENT_REGISTRY[agent_name]
            keys.append(state_key)
            coroutines.append(fn(query, profile))

    # 병렬 실행 (return_exceptions=True → 개별 실패가 전체를 중단시키지 않음)
    updated_results: Dict[str, Any] = {}
    if coroutines:
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        for key, res in zip(keys, results):
            if isinstance(res, Exception):
                print(f"[Orchestrator] {key} 오류: {res}")
                updated_results[key] = None
            else:
                updated_results[key] = res

    # 호출되지 않은 에이전트는 명시적으로 None 처리 (LLM 망상 방지)
    for state_key, _ in AGENT_REGISTRY.values():
        if state_key not in updated_results:
            updated_results[state_key] = None

    return updated_results


# ---------------------------------------------------------
# 2. 통합 LLM 노드 (LLM 호출 2번째)
# ---------------------------------------------------------
def unified_llm_node(state: GraphState) -> Dict[str, Any]:
    """
    에이전트 결과를 자연어 텍스트로 변환한 뒤 단일 프롬프트로 조립하여
    LUXIA 모델을 1회 호출합니다.
    """
    query = state.get("query", "")
    profile = state.get("user_profile", {})

    # 프로필 한국어 표현
    skills_str = ", ".join(profile.get("skills", [])) or "정보 없음"
    profile_text = (
        f"{profile.get('age', '?')}세, "
        f"{profile.get('region', '지역 미상')}, "
        f"중위소득 {profile.get('income_level', '?')}, "
        f"보유 기술: {skills_str}, "
        f"희망 직무: {profile.get('target_role', '?')}"
    )

    # 고정 영역: 페르소나 + 사용자 정보
    prompt_parts = [
        "당신은 대한민국 청년들의 사회 진입을 돕는 전문 어시스턴트 'YouthPath'입니다.",
        "아래 [검색 결과]만을 근거로 자연스러운 한국어 답변을 작성하세요.\n",
        f"[사용자 질문]\n{query}\n",
        f"[사용자 프로필]\n{profile_text}\n",
        "[검색 결과]",
    ]

    # 동적 규칙 목록 (공통 규칙 + 에이전트별 규칙)
    rules = [
        "1. 친근하지만 전문적인 어조를 유지하세요.",
        "2. 각 항목 끝에는 출처를 대괄호로 인용하세요. (예: [출처: 온통청년 API])",
        "3. [검색 결과] 외의 정보는 절대 추측하거나 만들어내지 마세요.",
    ]
    rule_idx = 4

    # 동적 영역: 에이전트 결과 + 전용 규칙 조립
    if state.get("policy_result"):
        prompt_parts.append(
            f"--- 정책 부문 ---\n{format_policy_result(state['policy_result'])}\n"
        )
        rules.append(
            f"{rule_idx}. [정책] 자격 충족 항목이 많은 정책을 우선 추천하고, 마감이 임박하면 기한을 강조하세요."
        )
        rule_idx += 1
    else:
        prompt_parts.append("--- 정책 부문 ---\n(해당 결과 없음)\n")

    if state.get("job_result"):
        prompt_parts.append(
            f"--- 채용 부문 ---\n{format_job_result(state['job_result'])}\n"
        )
        rules.append(
            f"{rule_idx}. [채용] 적합도가 가장 높은 공고를 설명할 때 어떤 스킬이 매칭됐는지 언급하세요."
        )
        rule_idx += 1
    else:
        prompt_parts.append("--- 채용 부문 ---\n(해당 결과 없음)\n")

    if state.get("resume_result"):
        prompt_parts.append(
            f"--- 자소서 가이드 부문 ---\n{format_resume_result(state['resume_result'])}\n"
        )
        rules.append(
            f"{rule_idx}. [자소서] 보강 제안을 구체적으로 언급하며 어필 방향을 안내하세요."
        )
        rule_idx += 1
    else:
        prompt_parts.append("--- 자소서 가이드 부문 ---\n(해당 결과 없음)\n")

    if state.get("calendar_result"):
        prompt_parts.append(
            f"--- 일정 부문 ---\n{format_calendar_result(state['calendar_result'])}\n"
        )
        rules.append(
            f"{rule_idx}. [일정] D-day가 가장 짧은 일정을 첫 문단에서 우선 안내하세요."
        )
        rule_idx += 1
    else:
        prompt_parts.append("--- 일정 부문 ---\n(해당 결과 없음)\n")

    rules.append(
        f"{rule_idx}. 사용자가 즉시 행동할 수 있는 다음 단계(Call to Action)를 답변 마지막에 번호로 제시하세요."
    )
    rules.append(
        f"{rule_idx + 1}. '(해당 결과 없음)' 섹션은 답변에서 절대 언급하지 마세요."
    )

    prompt_parts.append("[답변 작성 규칙]\n" + "\n".join(rules))
    final_prompt = "\n".join(prompt_parts)

    # ---------------------------------------------------------
    # [TODO] LUXIA LLM 호출 — 연동 방식 확정 후 아래 중 하나 활성화
    # ---------------------------------------------------------
    # 방법 A: LangChain
    # from langchain_community.chat_models import ChatLUXIA
    # llm = ChatLUXIA(temperature=0.7)
    # response = llm.invoke([("user", final_prompt)])
    # final_answer = response.content

    # 방법 B: OpenAI 호환 엔드포인트
    # from openai import OpenAI
    # client = OpenAI(base_url="LUXIA_BASE_URL", api_key="LUXIA_API_KEY")
    # response = client.chat.completions.create(
    #     model="luxia-model-name",
    #     messages=[{"role": "user", "content": final_prompt}],
    # )
    # final_answer = response.choices[0].message.content

    # 임시: 조립된 프롬프트 출력으로 확인
    print("[Unified LLM] 프롬프트 조립 완료 (LLM 연동 대기 중)")
    print("=" * 60)
    print(final_prompt)
    print("=" * 60)

    return {"final_answer": "LLM 연동 대기 중. 위 프롬프트 확인 요망."}


# ---------------------------------------------------------
# 3. LangGraph 워크플로우 조립
# ---------------------------------------------------------
workflow = StateGraph(GraphState)

workflow.add_node("router", router_node)
workflow.add_node("agents_orchestrator", agents_orchestrator_node)
workflow.add_node("unified_llm", unified_llm_node)

workflow.set_entry_point("router")
workflow.add_edge("router", "agents_orchestrator")
workflow.add_edge("agents_orchestrator", "unified_llm")
workflow.add_edge("unified_llm", END)

app = workflow.compile()


# ---------------------------------------------------------
# 로컬 테스트
# ---------------------------------------------------------
if __name__ == "__main__":
    initial_state = {
        "query": "서울에서 월세 도와주는 정책이랑 IT 신입 공고 알려줘",
        "user_profile": {
            "age": 27,
            "region": "서울",
            "income_level": "60% 이하",
            "skills": ["Python", "SQL"],
            "target_role": "데이터 분석가",
            "target_company": "네이버",
        },
    }

    print("[System] YouthPath LangGraph 파이프라인 시작")
    final_output = asyncio.run(app.ainvoke(initial_state))

    print("\n================== [최종 출력 결과] ==================")
    print(final_output["final_answer"])
