from typing import TypedDict, Optional, Any

class GraphState(TypedDict):
    """
    LangGraph의 모든 노드(에이전트)가 주고받는 전역 상태 데이터입니다.
    """
    # 1. 사용자 입력 및 프로필
    query: str
    user_profile: dict
    
    # 2. 라우터 결정 사항
    # 예: {"agents": ["policy", "job"], "reasoning": "..."}
    router_decision: dict 
    
    # 3. 각 에이전트의 Raw JSON 결과 (빈 딕셔너리로 초기화)
    policy_result: Optional[dict]
    job_result: Optional[dict]
    resume_result: Optional[dict]
    calendar_result: Optional[dict]
    
    # 4. 통합 LLM의 최종 자연어 응답
    final_answer: Optional[str]
    