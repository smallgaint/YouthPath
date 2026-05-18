import asyncio
from typing import Dict, Any
from langgraph.graph import StateGraph, END

# 앞서 정의한 모듈들 임포트
from state import GraphState
from router import router_node
from formatters import (
    format_policy_result,
    format_job_result,
    format_resume_result,
    format_calendar_result
)

# ---------------------------------------------------------
# 1. 에이전트 병렬 실행 오케스트레이터 노드
# ---------------------------------------------------------
async def agents_orchestrator_node(state: GraphState) -> Dict[str, Any]:
    """
    라우터의 결정에 따라 선택된 에이전트들을 asyncio.gather로 
    동시에 병렬 실행하고 결과를 수집합니다.
    """
    decision = state.get("router_decision", {})
    active_agents = decision.get("agents", [])
    
    # 에이전트별 비동기 작업(Task)을 담을 딕셔너리
    tasks = {}
    
    # [참고] 각 도메인 팀원들이 완성한 비동기 함수(예: async def run_xxx_agent)를 
    # 여기에 연결해야 합니다. 지금은 스켈레톤 상태로 구조화합니다.
    
    if "policy" in active_agents:
        # tasks["policy_result"] = run_policy_agent(state["query"], state["user_profile"])
        print("[System] Policy Agent 작업 예약")
        pass
        
    if "job" in active_agents:
        # tasks["job_result"] = run_job_agent(state["query"], state["user_profile"])
        print("[System] Job Agent 작업 예약")
        pass
        
    # if "resume" in active_agents:
    #     # tasks["resume_result"] = run_resume_agent(state["query"], state["user_profile"])
    #     print("[System] Resume Agent 작업 예약")
    #     pass
        
    # if "calendar" in active_agents:
    #     # tasks["calendar_result"] = run_calendar_agent(state["query"], state["user_profile"])
    #     print("[System] Calendar Agent 작업 예약")
    #     pass

    # 호출할 에이전트가 있다면 병렬 실행 [cite: 68]
    updated_results = {}
    if tasks:
        # keys와 coroutines 분리하여 gather 실행
        keys = list(tasks.keys())
        coroutines = list(tasks.values())
        
        # 실제로 각 에이전트가 코드로 데이터를 모아오는 구간 (외부 HTTP 호출) [cite: 67, 68]
        results = await asyncio.gather(*coroutines)
        
        # 결과를 상태 변수명에 맞게 매핑
        for key, res in zip(keys, results):
            updated_results[key] = res
            
    # 호출되지 않은 에이전트 자리는 명시적으로 None 처리하여 망상 방지 [cite: 270, 399]
    all_agent_keys = ["policy_result", "job_result", "resume_result", "calendar_result"]
    for key in all_agent_keys:
        if key not in updated_results:
            updated_results[key] = None
            
    return updated_results

# ---------------------------------------------------------
# 2. 통합 LLM 노드 (최종 답변 생성 및 페르소나 주입)
# ---------------------------------------------------------
def unified_llm_node(state: GraphState) -> Dict[str, Any]:
    """
    실행된 에이전트의 결과에 따라 프롬프트와 지시사항을 동적으로 조립하여 
    LUXIA 모델을 1회 호출합니다.
    """
    query = state.get("query", "")
    profile = state.get("user_profile", {})
    
    # 1. 고정 영역: 페르소나 및 사용자 정보
    prompt_parts = [
        "당신은 대한민국 청년들의 사회 진입을 돕는 든든하고 전문적인 어시스턴트 'YouthPath'입니다.",
        "아래 제공된 [사용자 질문], [프로필], [검색 결과]를 바탕으로 자연스러운 한국어 답변을 작성하세요.\n",
        f"[사용자 질문]\n{query}\n",
        f"[사용자 프로필]\n{profile}\n",
        "[검색 결과]"
    ]
    
    # 2. 동적 영역: 컨텍스트 추가 및 전용 지시사항(Rules) 세팅
    rules = [
        "1. 친근하지만 전문적인 어조를 유지하세요.",
        "2. 각 항목 끝에는 반드시 대괄호를 사용하여 출처를 인용하세요. (예: [출처: 온통청년 API])",
        "3. 제공된 정보에 없는 사실은 절대로 지어내거나 추측하여 작성하지 마세요."
    ]
    rule_idx = 4 # 공통 규칙 다음 번호부터 시작
    
    # --- 정책(Policy) 에이전트가 실행되었을 때 ---
    if state.get("policy_result"):
        policy_text = format_policy_result(state["policy_result"])
        prompt_parts.append(f"--- 정책 부문 ---\n{policy_text}\n")
        
        # 정책 전용 프롬프트 규칙 추가
        rules.append(f"{rule_idx}. [정책 규칙] 자격 충족(matched) 항목이 많은 정책을 우선적으로 추천하고, 마감일이 임박했다면 기한을 강조하세요.")
        rule_idx += 1

    # --- 채용(Job) 에이전트가 실행되었을 때 ---
    if state.get("job_result"):
        job_text = format_job_result(state["job_result"])
        prompt_parts.append(f"--- 채용 부문 ---\n{job_text}\n")
        
        # 채용 전용 프롬프트 규칙 추가
        rules.append(f"{rule_idx}. [채용 규칙] 적합도(%)가 가장 높은 회사를 언급할 때, 사용자의 어떤 스킬이 매칭되었는지 간략히 설명하세요.")
        rule_idx += 1

    # --- 자소서(Resume) 에이전트가 실행되었을 때 ---
    if state.get("resume_result"):
        resume_text = format_resume_result(state["resume_result"])
        prompt_parts.append(f"--- 자소서 가이드 부문 ---\n{resume_text}\n")
        
        rules.append(f"{rule_idx}. [자소서 규칙] 보강 제안(evidence_gaps)을 언급하며, 어떤 경험을 더 어필하면 좋을지 구체적인 가이드를 주세요.")
        rule_idx += 1

    # --- 일정(Calendar) 에이전트가 실행되었을 때 ---
    if state.get("calendar_result"):
        calendar_text = format_calendar_result(state["calendar_result"])
        prompt_parts.append(f"--- 일정 부문 ---\n{calendar_text}\n")
        
        rules.append(f"{rule_idx}. [일정 규칙] 남은 D-day를 기준으로 가장 시급하게 처리해야 할 일정을 첫 문단에서 상기시켜 주세요.")
        rule_idx += 1

    # 3. 마무리 영역: 규칙 조립
    rules.append(f"{rule_idx}. 사용자가 즉시 실행할 수 있는 구체적인 다음 단계(Call to Action)를 답변 마지막에 순서대로 명시하세요.")
    
    prompt_parts.append("[답변 작성 규칙]")
    prompt_parts.append("\n".join(rules))
    
    # 4. 최종 프롬프트 문자열 완성
    final_prompt = "\n".join(prompt_parts)
    
    # 디버깅용: 조립된 프롬프트 확인
    # print("========== [동적 프롬프트 생성 결과] ==========")
    # print(final_prompt)
    # print("===============================================")
    
    # ---------------------------------------------------------
    # LUXIA LLM API 호출 부분 연결
    # ---------------------------------------------------------
    # response = luxia_client.generate(final_prompt)
    # final_answer = response.text
    
    # 임시 반환값
    return {"final_answer": "동적 프롬프트 조립이 완료되었습니다. (LLM 연동 대기 중)"}


# ---------------------------------------------------------
# 3. LangGraph Workflow 파이프라인 조립
# ---------------------------------------------------------
workflow = StateGraph(GraphState)

# 노드 등록
workflow.add_node("router", router_node)
workflow.add_node("agents_orchestrator", agents_orchestrator_node)
workflow.add_node("unified_llm", unified_llm_node)

# 그래프 흐름(Edge) 연결
workflow.set_entry_point("router")
workflow.add_edge("router", "agents_orchestrator")
workflow.add_edge("agents_orchestrator", "unified_llm")
workflow.add_edge("unified_llm", END)

# 최종 컴파일
app = workflow.compile()

# ---------------------------------------------------------
# 파이프라인 작동 테스트 구문 (로컬 실행용)
# ---------------------------------------------------------
if __name__ == "__main__":
    # FastAPI 백엔드가 받아서 넘겨줄 요청 가상 주입
    initial_state = {
        "query": "서울에서 월세 도와주는 정책이랑 IT 신입 공고 알려줘", [cite: 25]
        "user_profile": { [cite: 27]
            "age": 27,
            "region": "서울",
            "skills": ["Python", "SQL"],
            "target_role": "데이터 분석가"
        }
    }
    
    # 비동기 그래프 실행
    print("[System] YouthPath LangGraph 런타임 시작")
    final_output = asyncio.run(app.ainvoke(initial_state))
    
    print("\n================== [최종 출력 결과] ==================\n")
    print(final_output["final_answer"])