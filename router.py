import json
from typing import List
from pydantic import BaseModel, Field
# 팀에서 사용하는 LUXIA API 래퍼나 LangChain Chat 모델을 임포트해야 합니다.
# from langchain_community.chat_models import ChatLUXIA 

# ---------------------------------------------------------
# 1. 라우터 출력 스키마 정의 (가장 중요)
# LLM이 다른 헛소리 없이 정확히 이 구조로만 대답하도록 강제합니다.
# ---------------------------------------------------------
class RouterOutput(BaseModel):
    agents: List[str] = Field(
        description="호출할 에이전트 목록. policy, job, resume, calendar 중 선택."
    )
    reasoning: str = Field(
        description="해당 에이전트들을 선택한 이유를 짧게 작성"
    )

# ---------------------------------------------------------
# 2. 라우터 노드 함수
# LangGraph의 State를 인자로 받아 라우팅 결과를 반환합니다.
# ---------------------------------------------------------
def router_node(state: dict) -> dict:
    """
    사용자의 질문을 분석하여 어떤 에이전트를 병렬로 실행할지 결정합니다.
    """
    user_query = state.get("query", "")
    
    # 시스템 프롬프트 구성 (기획서 기반)
    system_prompt = f"""
    당신은 사용자 질의를 분석하여 호출할 에이전트를 모두 선택하는 라우터입니다[cite: 52].
    
    [에이전트 목록 및 역할]
    - policy: 청년 정책, 지원금, 복지 [cite: 54]
    - job: 채용공고, 직무, 회사 추천 [cite: 55]
    - resume: 자소서 가이드 [cite: 56]
    - calendar: 마감일, 일정 [cite: 57]
    
    사용자 질의를 분석하여 필요한 에이전트를 JSON 형식으로만 응답하세요.
    """

    # ---------------------------------------------------------
    # [TO-DO] LUXIA 모델 호출 부분 (팀의 API 연동 방식에 맞춰 수정 필요)
    # ---------------------------------------------------------
    # 예시: LangChain의 with_structured_output을 사용하는 경우
    # llm = ChatLUXIA(temperature=0)
    # structured_llm = llm.with_structured_output(RouterOutput)
    # result = structured_llm.invoke([
    #     ("system", system_prompt),
    #     ("human", user_query)
    # ])
    
    # 임시 Mock Data (API 연동 전 테스트용)
    print("라우터 분석 중: ", user_query)
    mock_response = RouterOutput(
        agents=["policy", "job"], 
        reasoning="월세 지원 정책과 IT 신입 채용 공고를 동시에 요청함 [cite: 61]"
    )
    
    # LangGraph의 State를 업데이트하기 위해 딕셔너리 반환
    return {"router_decision": mock_response.dict()}