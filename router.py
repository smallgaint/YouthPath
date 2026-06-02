import json
from typing import List
from pydantic import BaseModel, Field

# [TODO] LUXIA 연동 시 아래 중 팀 방식에 맞는 임포트 사용
# from langchain_community.chat_models import ChatLUXIA
# from openai import OpenAI  # base_url + api_key로 LUXIA 엔드포인트 지정

VALID_AGENTS = {"policy", "job", "resume", "calendar"}

# ---------------------------------------------------------
# 1. 라우터 출력 스키마 (LLM이 이 구조로만 응답하도록 강제)
# ---------------------------------------------------------
class RouterOutput(BaseModel):
    agents: List[str] = Field(
        description="호출할 에이전트 목록. policy, job, resume, calendar 중 선택."
    )
    reasoning: str = Field(
        description="해당 에이전트들을 선택한 이유를 짧게 작성"
    )

ROUTER_SYSTEM_PROMPT = """당신은 사용자 질의를 분석하여 호출할 에이전트를 선택하는 라우터입니다.

[에이전트 목록]
- policy: 청년 정책, 지원금, 복지 혜택
- job: 채용공고, 직무, 회사 추천
- resume: 자소서 가이드, 취업 서류
- calendar: 마감일, 일정 관리

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.
{"agents": ["에이전트1", "에이전트2"], "reasoning": "선택 이유"}"""

# ---------------------------------------------------------
# 2. 라우터 노드 함수
# ---------------------------------------------------------
def router_node(state: dict) -> dict:
    """
    사용자의 질문을 분석하여 어떤 에이전트를 병렬로 실행할지 결정합니다.
    LLM을 1회 호출하여 JSON 형식으로 라우팅 결정을 받습니다.
    """
    user_query = state.get("query", "")

    # ---------------------------------------------------------
    # [TODO] LUXIA LLM 호출 - 연동 방식 확정 후 아래 중 하나 활성화
    # ---------------------------------------------------------
    # 방법 A: LangChain with_structured_output
    # llm = ChatLUXIA(temperature=0)
    # structured_llm = llm.with_structured_output(RouterOutput)
    # result = structured_llm.invoke([
    #     ("system", ROUTER_SYSTEM_PROMPT),
    #     ("human", user_query)
    # ])
    # router_decision = result.dict()

    # 방법 B: OpenAI 호환 엔드포인트 직접 호출
    # client = OpenAI(base_url="LUXIA_BASE_URL", api_key="LUXIA_API_KEY")
    # response = client.chat.completions.create(
    #     model="luxia-model-name",
    #     messages=[
    #         {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
    #         {"role": "user", "content": user_query},
    #     ],
    #     temperature=0,
    # )
    # raw = response.choices[0].message.content
    # router_decision = RouterOutput(**json.loads(raw)).dict()

    # ---------------------------------------------------------
    # 임시 Mock (LLM 연동 전 테스트용) — 연동 후 위 코드로 교체
    # ---------------------------------------------------------
    print(f"[Router] 질의 분석 중: {user_query}")
    mock_response = RouterOutput(
        agents=["policy", "job"],
        reasoning="월세 지원 정책과 IT 신입 채용 공고를 동시에 요청함"
    )
    router_decision = mock_response.dict()

    # LLM이 잘못된 에이전트 이름을 반환할 경우 필터링
    router_decision["agents"] = [
        a for a in router_decision["agents"] if a in VALID_AGENTS
    ]

    print(f"[Router] 선택된 에이전트: {router_decision['agents']}")
    return {"router_decision": router_decision}