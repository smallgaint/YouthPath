# YouthPath Router

LangGraph Router 통합을 위한 Router 패키지입니다.

## 현재 구성
- `router.py`: Router 오케스트레이션
- `agents.py`: Policy / Job / Resume / Calendar 래퍼
- `formatters.py`: Agent JSON -> 텍스트 변환
- `llm_provider.py`: LUXIA 추상 인터페이스 + mock/real provider + 환경변수 기반 선택
- `schemas.py`: 요청/상태/응답 공통 스키마
- `main.py`: 로컬 실행용 샘플 엔트리포인트

## 실행
```bash
python -m Router.main
```

## LUXIA 전환

기본값은 mock provider입니다. LUXIA API가 발급되면 `.env`에 아래 값을 채우고 서버를 재시작하세요.

```env
YOUTHPATH_LLM_PROVIDER=luxia
LUXIA_API_URL=https://bridge.luxiacloud.com/luxia/v1/chat
LUXIA_API_KEY=...
LUXIA_MODEL=luxia3-llm-32b-0731
LUXIA_TIMEOUT=60
LUXIA_REQUEST_FORMAT=openai
LUXIA_AUTH_HEADER=apikey
LUXIA_AUTH_SCHEME=
LUXIA_INCLUDE_GENERATION_PARAMS=false
LUXIA_FALLBACK_TO_MOCK=true
```

- `openai` 형식은 `messages` 기반 payload를 보냅니다.
- `generic` 형식은 `{model, prompt, temperature, max_tokens}` payload를 보냅니다.
- 응답은 `choices[0].message.content`, `choices[0].text`, `answer`, `content`, `text`, `result`, `response` 순서로 파싱합니다.

LUXIA는 Router의 두 지점에 쓰입니다.
- 첫 호출: 사용자 질의를 `policy/job/resume/calendar`로 분류
- 마지막 호출: 에이전트 결과를 자연어 `answer`로 통합

구조화된 `policy`, `job`, `resume`, `calendar`, `metadata` JSON은 프론트 렌더링용으로 계속 유지합니다.
