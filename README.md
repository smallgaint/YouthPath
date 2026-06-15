# YouthPath 🧭

청년 사회진입을 돕는 **멀티 에이전트 서비스**입니다. 사용자가 한 번 질의하면 **Router**가 의도를 분석해 정책 · 채용 · 이력서(자소서) · 일정 에이전트를 선택 실행하고, 결과를 하나의 통합 응답으로 합쳐 **FastAPI + Streamlit** 앱으로 보여줍니다.

> 한 줄 질문 → 정책/채용/자소서/마감일정을 한 화면에.

---

## 🎬 시연 영상

- ▶️ 시연 영상: (docs/demo.mp4)

---

## ✨ 주요 기능

| 에이전트 | 데이터 소스 | 설명 |
|---------|------------|------|
| **Policy** | 온통청년 정책 API + RAG | 청년 정책·지원금·주거 등 추천 (프로필 기반 점수화) |
| **Job** | 공공데이터포털 채용공고 API | 실제 채용 공고 + 마감일/D-day |
| **Resume** | DART 공시 + NAVER 뉴스 | 지원 기업 분석 기반 자소서 작성 프롬프트 |
| **Calendar** | 정책·채용 마감일 병합 | 마감 일정 통합 + 마이페이지 캘린더 |
| **LLM** | LUXIA (실패 시 Mock 폴백) | 질의 분류 + 자연어 답변 통합 |

---

## 🚀 빠른 시작 (macOS / Linux)

### 1. 가상환경 + 의존성

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r A/requirements.txt numpy OpenDartReader \
  beautifulsoup4 lxml scikit-learn keybert fastapi uvicorn streamlit pandas
```

### 2. 환경변수 설정

```bash
cp .env.sample .env
# .env 파일을 열어 발급받은 API 키를 채웁니다. (자세한 항목은 .env.sample 주석 참고)
```

> 키가 없어도 동작합니다 — 해당 에이전트는 폴백/mock으로 응답하고, 실패 사유는 응답의 `metadata.agent_errors`에 기록됩니다.

### 3. (선택) Resume 기업 공시 인덱싱

Resume 에이전트는 **사전 인덱싱된 기업**의 DART 공시만 사용합니다. 보고 싶은 기업을 먼저 인덱싱하세요.

```bash
.venv/bin/python index_company.py 네이버 035420
.venv/bin/python index_company.py 카카오 035720
# 인자: <profile.target_company 와 일치할 이름> <DART 식별자(종목코드/회사명)> [start_date]
```

### 4. 백엔드(FastAPI) 실행

```bash
cd YouthPath-jaewon/YouthPath-jaewon
../../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
# API 문서: http://127.0.0.1:8000/docs
```

### 5. 프론트엔드(Streamlit) 실행

새 터미널에서:

```bash
cd YouthPath-jaewon/YouthPath-jaewon
../../.venv/bin/streamlit run app.py
# 앱: http://localhost:8501
```

---

## 📁 폴더 구조

```text
Router/              # Router 오케스트레이션, LUXIA provider 어댑터
A/                   # Policy Agent: 온통청년 API, RAG, 로컬 정책 데이터
YouthPath-Huiseung/  # Job Agent (공공데이터/워크넷 채용)
YouthPath-Jeonghyun/ # Resume Agent (DART 공시 + NAVER 뉴스 파이프라인)
YouthPath-jaewon/    # FastAPI 백엔드 + Streamlit 프론트엔드
index_company.py     # DART 공시를 Chroma에 사전 인덱싱하는 스크립트
.env.sample          # 환경변수 템플릿 (복사해서 .env 작성)
```

---

## 🔌 API: `POST /ask`

```jsonc
// 요청
{
  "query": "서울 청년 월세 정책이랑 IT 신입 공고 알려줘",
  "profile": { "age": 27, "region": "서울", "skills": ["Python"], "target_company": "네이버" }
}

// 응답
{
  "answer": "LUXIA가 생성한 자연어 답변",
  "policy": [], "job": [], "resume": [], "calendar": [],
  "metadata": { "classification": {}, "llm_provider": "LuxiaProvider", "agent_errors": {} },
  "error": null
}
```

`policy/job/resume/calendar` 배열은 프론트엔드 카드 렌더링용 구조화 데이터입니다.

---

## 🧠 LLM (LUXIA) 동작

Router는 LLM provider를 두 번 호출합니다.

1. **분류**: 질의를 보고 `policy / job / resume / calendar` 중 실행할 에이전트 선택
2. **통합 답변**: 에이전트 결과를 자연어 `answer`로 합침

`.env`에 `YOUTHPATH_LLM_PROVIDER=luxia` 와 `LUXIA_API_*` 를 채우면 실제 LUXIA를 사용하고, **LUXIA 장애 시 자동으로 Mock 답변으로 폴백**합니다(`LUXIA_FALLBACK_TO_MOCK=true`). 이때도 정책/채용/자소서/일정 카드는 실데이터로 그대로 표시됩니다.

---

## 🚀 배포 (클라우드 VM)

클라우드 VM(AWS EC2 / GCP)에 올리는 단계별 가이드는 **[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)** 를 참고하세요.
(VM 사양·포트·`.env`·systemd 자동 실행·nginx 리버스 프록시·비용/스왑 팁 포함)

---

## ⚠️ 보안 주의

- **`.env`, `users.json`은 절대 커밋하지 마세요** (`.gitignore`로 제외됨). API 키·비밀번호가 포함됩니다.
- 공개 저장소에 푸시하기 전 `git status`로 민감 파일이 staged 되지 않았는지 확인하세요.
