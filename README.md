# YouthPath

YouthPath는 청년 사회진입을 돕는 멀티 에이전트 서비스입니다. 사용자가 한 번 질의하면 Router가 의도를 분석해 정책, 채용, 이력서/자소서, 일정 에이전트를 선택 실행하고, FastAPI와 Streamlit 앱에서 사용할 수 있는 통합 응답으로 합칩니다.

## 현재 상태

- `Router/` 패키지가 Jaewon FastAPI `/ask` 엔드포인트에 연결되어 있습니다.
- Policy는 `A.services.policy_service`를 사용하며 온통청년 API, RAG, 로컬 JSON 폴백 경로를 갖습니다.
- Job은 Worknet 실 API를 먼저 시도하고 실패하면 검증용 샘플 데이터로 폴백합니다.
- Resume은 Jeonghyun의 DART/Naver 파이프라인을 먼저 시도하고 실패하면 룰 기반 자소서 컨텍스트로 폴백합니다.
- Calendar는 정책/채용 결과의 마감일을 통합합니다.
- LUXIA API는 아직 실연동 전입니다. 대신 `LuxiaProvider` 어댑터가 준비되어 있어 `.env` 값만 채우면 mock에서 실제 LUXIA로 전환됩니다.

## 폴더 구조

```text
Router/                         # Router 오케스트레이션, LUXIA provider 어댑터
A/                              # Policy Agent: 온통청년 API, RAG, 로컬 정책 데이터
YouthPath-Huiseung/             # Job Agent 원본/워크넷 구현
YouthPath-Jeonghyun/            # Resume Agent 원본/DART+Naver 구현
YouthPath-jaewon/               # FastAPI 백엔드, Streamlit 프론트엔드
docs/YouthPath_architecture.md  # 통합 아키텍처와 진행 현황
worklog.md                      # 다음 작업자를 위한 작업 로그
tmp_verify_e2e.py               # 파일 기반 E2E 검증 스크립트
```

## 환경 설정

통합 실행은 프로젝트 가상환경을 기준으로 합니다.

```powershell
.\.venv\Scripts\python.exe --version
```

프로젝트는 루트의 `.env`를 읽습니다. 로컬 mock 실행에는 정책 API 키만 있어도 됩니다. LUXIA 관련 값은 API가 발급된 뒤 주석을 해제해 채우면 됩니다.

```env
ONTONG_API_KEY=...

# LUXIA API 발급 후 사용
# YOUTHPATH_LLM_PROVIDER=luxia
# LUXIA_API_URL=https://.../v1/chat/completions
# LUXIA_API_KEY=...
# LUXIA_MODEL=luxia
# LUXIA_REQUEST_FORMAT=openai
# LUXIA_FALLBACK_TO_MOCK=true
```

## E2E 검증

프로젝트 루트에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe tmp_verify_e2e.py
```

검증 시나리오:

- `job+resume`: Router와 FastAPI 경로에서 Job/Resume 분기 검증
- `policy+job+resume+calendar`: Policy 분기와 마감일 Calendar 병합 검증

현재 알려진 폴백:

- `.venv`에 `OpenDartReader`가 없으면 Resume 실 DART/Naver 파이프라인은 실행되지 않고 룰 기반 컨텍스트로 폴백합니다.
- 이 경우 실패 이유는 응답의 `metadata.agent_errors`에 기록됩니다.

## Router 단독 실행

```powershell
.\.venv\Scripts\python.exe -m Router.main
```

샘플 요청에 대한 통합 Router JSON 응답을 출력합니다.

## FastAPI 백엔드 실행

`YouthPath-jaewon` 폴더명에 하이픈이 있어, 백엔드 폴더 안에서 `uvicorn`을 실행하는 방식이 가장 안정적입니다.

```powershell
cd YouthPath-jaewon\YouthPath-jaewon
..\..\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

실행 후 아래 주소에서 API 문서를 확인할 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

## Streamlit 프론트엔드 실행

먼저 FastAPI 백엔드를 실행한 뒤, 새 터미널을 열어 프로젝트 루트에서 실행합니다.

```powershell
.\.venv\Scripts\streamlit.exe run YouthPath-jaewon\YouthPath-jaewon\app.py
```

Streamlit 앱은 아래 FastAPI 엔드포인트로 `POST /ask` 요청을 보냅니다.

```text
http://127.0.0.1:8000/ask
```

## LUXIA 전환 방법

Router는 LLM provider를 두 번 호출합니다.

1. 분류 호출: 사용자 질의를 보고 `policy`, `job`, `resume`, `calendar` 중 실행할 에이전트 선택
2. 최종 응답 호출: 에이전트 결과를 자연어 `answer`로 통합

현재는 `MockLuxiaProvider`가 두 역할을 대신합니다. LUXIA API가 발급되면 `.env`에 아래 값을 설정합니다.

```env
YOUTHPATH_LLM_PROVIDER=luxia
LUXIA_API_URL=...
LUXIA_API_KEY=...
```

그 다음 FastAPI를 재시작하면 실제 LUXIA Provider가 자동 선택됩니다. 응답 구조는 그대로 유지됩니다.

```json
{
  "answer": "LUXIA가 생성한 자연어 답변",
  "policy": [],
  "job": [],
  "resume": [],
  "calendar": [],
  "metadata": {},
  "error": null
}
```

`policy`, `job`, `resume`, `calendar` 배열은 프론트엔드 카드 렌더링용 구조화 데이터이므로 LUXIA 실연동 후에도 유지합니다.
