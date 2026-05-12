# YouthPath 프로젝트 피드백 정리 및 답변

> 딥러닝 및 응용 — Team 10 YouthPath 프로젝트 제안 발표 후 받은 피드백 11개를 정리한 문서입니다.
> 각 피드백은 **(1) 영문 원문**, **(2) 한글 번역**, **(3) 질문 의도**, **(4) 답변 및 대응 방안** 순서로 정리되어 있습니다.

---

## 📌 사전 정리: Q5의 "베이스라인을 나눈다"는 의미

본격적인 답변에 앞서, Q5 피드백에서 언급된 **"베이스라인 분리"**의 의미를 먼저 명확히 합니다.

"베이스라인을 나눈다"는 것은 **전체 파이프라인을 3개로 쪼개서 운영한다**는 뜻이 아닙니다. 최종 시스템(YouthPath)은 그대로 하나로 유지하되, **평가 실험을 진행할 때만 비교용으로 단순화 버전을 추가로 돌려서 점수를 비교**한다는 의미입니다.

비유하자면 신약 효과 검증 시 "약 안 먹은 그룹 vs 약 먹은 그룹"으로 나누는 것과 같습니다. 우리 프로젝트에서는:

| 베이스라인 | 구성 | 측정 목적 |
|---|---|---|
| **B1** | LLM only (단일 모델 답변) | 가장 단순한 기준선 |
| **B2** | LLM + RAG (Agent 없이, 모든 자료를 한 통에 넣고 검색) | RAG의 효과 측정 |
| **B3** | LLM + RAG + Multi-Agent (= YouthPath) | Agent 구조의 효과 측정 |

평가 데이터셋(50문항)을 이 3개 시스템에 똑같이 던져서 정확도/응답시간/만족도를 비교하면:

- **B1 → B2 차이 = RAG가 기여한 정도**
- **B2 → B3 차이 = Multi-Agent 구조가 기여한 정도**

이렇게 나누면 "Multi-Agent를 쓴 게 정말 의미 있었는가?"를 숫자로 증명할 수 있습니다. 원래 제안서에는 B1 vs B3만 있어서 "RAG 덕분인지 Agent 덕분인지" 구분이 안 되니, B2를 추가하라는 것이 피드백의 핵심입니다.

ML 분야에서는 이를 **Ablation Study(절제 실험)** — 시스템의 일부 구성요소를 제거하고 돌려보면서 그 부분의 기여도를 측정하는 실험 — 이라고 부릅니다.

---

## Q1. LLM 모델을 3개 쓰는 이유

### 영문 원문
> What is the purpose of using 3 types of llm models? Couldn't a single model handle everything?

### 한글 번역
3가지 LLM 모델을 사용하는 목적이 무엇인가요? 단일 모델로 모든 것을 처리할 수는 없나요?

### 질문 의도
복잡도를 높이지 말고 모델을 하나로 통일하지 그랬느냐는 의문입니다. 각 모델별 역할 분담의 명확한 근거를 요구하는 질문입니다.

### 답변
각 모델은 **잘하는 영역과 가격이 다르며**, "도구별 최적화" 논리로 답변할 수 있습니다.

- **LUXIA**: 한국어 답변 톤이 자연스럽고 수업에서 크레딧을 제공받음 → **메인 답변 생성용**으로 사용
- **Gemini 2.0 Flash**: 컨텍스트 200만 토큰까지 처리 가능 → **긴 DART 사업보고서를 통째로 넣어야 할 때만** 사용 (LUXIA로는 토큰 한계로 처리 불가). 무료 tier 활용
- **GPT-4o-mini**: **평가(LLM-as-judge)용**. 평가자는 답변 생성자와 분리되어야 공정함이 보장되므로, 답변은 LUXIA가 만들고 채점은 GPT가 하는 분리 구조

**핵심 답변**: 단일 모델로도 가능하지만, 비용·속도·강점이 모두 다르므로 역할별로 가장 효율적인 모델을 배정하는 것이 합리적입니다. 모든 호출에 GPT-4를 쓰면 비용이 폭증하고, 모든 호출에 LUXIA를 쓰면 긴 문서 처리가 불가능합니다.

---

## Q2. 빠르게 변하는 정보의 실시간 반영

### 영문 원문
> Information in the news and stock market changes rapidly, how can verified data be reflected in real time?

### 한글 번역
뉴스와 주식 시장 정보는 빠르게 변하는데, 검증된 데이터를 어떻게 실시간으로 반영할 수 있나요?

### 질문 의도
RAG 방식이 진짜 실시간성을 보장할 수 있는지, 그리고 그 정보가 신뢰할 만한지에 대한 의문입니다.

### 답변
데이터 종류별로 **갱신 주기를 다르게 설계**합니다.

- **빠른 변동 데이터(채용공고, 뉴스)**: RAG에 저장하지 않습니다. **MCP로 매번 실시간 호출** (워크넷 API, 네이버 뉴스 API). 호출하는 그 순간이 곧 최신 데이터
- **중간 변동 데이터(정책)**: Static RAG에 저장하되 **주 1회 자동 재인덱싱** 스케줄러(cron job 등) 설정
- **희귀 변동 데이터(합격 자소서, NCS 평가기준)**: 1회 인덱싱 후 거의 바꾸지 않음

**검증된 데이터**를 위한 장치:

1. 출처를 **정부 공식 API(온통청년, DART, 워크넷)로만 한정**하여 신뢰성 확보
2. 답변 생성 시 **출처 인용(citation)을 함께 표시**하여 사용자가 직접 확인 가능
3. 응답 시점을 같이 표기 ("2026-05-09 기준")

---

## Q3. 외부 API 다운 시 fallback 계획

### 영문 원문
> Your project utilizes Dynamic RAG and MCP to fetch real-time data from external APIs like Worknet and DART. However, external APIs can often experience unexpected latency or downtime. Do you have any fallback plans or exception-handling architecture to ensure that users still receive stable services without missing critical information when such API issues occur?

### 한글 번역
프로젝트가 Dynamic RAG와 MCP를 활용해 워크넷, DART 같은 외부 API에서 실시간 데이터를 가져오는데, 외부 API는 종종 예기치 않은 지연이나 다운타임을 겪을 수 있습니다. API 문제 발생 시에도 사용자가 핵심 정보를 놓치지 않고 안정적인 서비스를 받을 수 있도록 하는 fallback 계획이나 예외 처리 아키텍처가 있나요?

### 질문 의도
시스템 안정성에 대한 구체적인 설계 검증입니다. "잘 작동할 때"뿐 아니라 "장애 상황에서도" 어떻게 동작하는지 답해야 합니다.

### 답변
**4단계 방어선**으로 안정성을 확보합니다.

1. **재시도(Retry with exponential backoff)**: API 호출 실패 시 1초 → 2초 → 4초 간격으로 재시도. 일시적 네트워크 문제는 대부분 이 단계에서 해결됨
2. **캐싱(Caching)**: 마지막으로 성공한 응답을 Redis나 로컬 파일에 저장. API가 죽었을 때 캐시 값 반환 + "정보 갱신: 어제 22:00 기준" 안내 표시
3. **회로 차단기(Circuit Breaker)**: API가 연속으로 실패하면 일정 시간 호출 자체를 차단. 시스템 부하 방지 + 복구 후 자동 재개
4. **다중 소스(Redundancy)**: 채용 정보는 워크넷 + 사람인 두 군데에서 가져오므로, 한쪽이 다운돼도 다른 쪽으로 대체 가능

**사용자 경험 측면 - Graceful Degradation**: 완전 실패 시에도 "현재 채용 정보를 가져올 수 없습니다. 정책 정보만 보여드릴게요"처럼 **부분 응답**을 제공하도록 설계하여, 모든 기능이 동시에 죽는 상황을 방지합니다.

---

## Q4. Router의 다중 Agent 처리 (병렬 vs 순차)

### 영문 원문
> How does the router agent handle queries that span multiple agents simultaneously — for example, a question combining job search and policy eligibility at the same time? Does it run agents in parallel or sequentially?

### 한글 번역
Router Agent는 여러 에이전트를 동시에 필요로 하는 질의를 어떻게 처리하나요? 예를 들어 채용 검색과 정책 자격을 동시에 묻는 질문 같은 것입니다. 에이전트를 병렬로 실행하나요, 순차로 실행하나요?

### 질문 의도
"취업 + 정책을 같이 알려줘"와 같은 복합 질의의 처리 방식, 그리고 응답 속도 최적화 전략에 대한 질문입니다.

### 답변
**의존성 여부에 따라 병렬/순차를 동적으로 결정**합니다.

- **독립적인 Agent들 → 병렬 실행** (`asyncio.gather`로 동시 호출): Policy Agent와 Job Agent는 서로의 결과가 필요 없으므로 동시에 돌립니다. 응답 시간을 절반 이하로 단축할 수 있습니다.
- **의존 관계가 있는 Agent → 순차 실행**: Calendar Agent는 Policy/Job Agent의 결과(마감일들)가 있어야 일정을 만들 수 있으므로, 그 두 개가 끝난 후에 실행합니다.

LangGraph에서 그래프 구조로 표현하면:

```
Router → [Policy ‖ Job ‖ Essay]   ← 병렬 (독립적)
       → Calendar                  ← 순차 (앞 결과를 입력으로 받음)
       → 통합 응답
```

이런 구조 덕분에 사용자는 복합 질의에서도 전체 Agent를 순차 실행한 것보다 빠른 응답을 받을 수 있습니다.

---

## Q5. RAG-only 베이스라인 추가 제안

### 영문 원문
> If you compare a single LLM with a RAG+agent system, the structural difference is quite large, so performance gains may be expected. To better isolate and evaluate the effect of the agent itself, have you considered including a standard RAG model (without agents) as an additional baseline?

### 한글 번역
단일 LLM과 RAG+Agent 시스템을 비교하면 구조적 차이가 너무 커서 성능 향상이 예상될 수밖에 없습니다. Agent 자체의 효과를 더 잘 분리해서 평가하기 위해, 일반 RAG 모델(Agent 없는)을 추가 베이스라인으로 포함하는 것을 고려해본 적 있나요?

### 질문 의도
**매우 좋은 평가 설계 피드백**입니다. 현재 비교가 "단일 LLM vs RAG+Agent"라서 **성능 향상이 RAG 덕분인지, Agent 덕분인지 구분이 안 된다**는 지적입니다.

### 답변
지적해주신 대로, **3단계 베이스라인**으로 평가를 확장하겠습니다.

| 베이스라인 | 구성 | 측정 목적 |
|---|---|---|
| **B1** | LLM only | 가장 단순한 기준선 |
| **B2** | LLM + RAG (Agent 없음, 모든 자료를 한 통에 넣고 검색) | RAG 자체의 효과 |
| **B3** | LLM + RAG + Multi-Agent (= YouthPath) | Agent 분리·라우팅의 추가 효과 |

이를 통해:

- **B1 → B2 차이** = RAG의 기여도
- **B2 → B3 차이** = Multi-Agent 구조의 기여도

를 각각 분리해서 측정할 수 있습니다. 이는 ML 분야에서 **Ablation Study(절제 실험)**로 불리며, 시스템 구성요소의 기여도를 정량적으로 검증하는 표준 방법입니다. 피드백을 반영해 B2를 추가하여 실험 설계를 보강하겠습니다.

---

## Q6. 사용자의 입력과 출력 형태

### 영문 원문
> I really like your proposed system but I am curious of what input does the user need to give to the system and what kind of output will the user get from the system?

### 한글 번역
제안된 시스템이 마음에 들지만, 사용자가 시스템에 어떤 입력을 제공해야 하고 어떤 종류의 출력을 받게 될지 궁금합니다.

### 질문 의도
데모 시연 시 사용자 흐름이 명확한지, 즉 입출력의 구체성에 대한 확인입니다.

### 답변

**입력 (1회 등록 + 매번 질의)**:

- **프로필 (1회 등록)**: 나이, 거주지, 학력 및 전공, 보유 기술, 소득 구간, 희망 직무, 관심 회사
- **자연어 질의 (매번)**: 예) "서울 사는 25살 개발 지망인데 받을 만한 정책이랑 채용 추천해줘"
- **선택적 입력**: 자소서 초안 텍스트, 지원 회사명

**출력 (대시보드 형태)**:

- **정책 카드**: 정책명 / 자격 매칭률 / 혜택 / 신청 마감 / 신청 링크
- **채용 카드**: 회사명 / 직무 / 적합도 / 마감일 / 공고 링크
- **자소서 피드백**: 항목별 점수 + 개선 제안 + 회사 specific 키워드 반영 제안
- **캘린더**: 통합 일정 + D-day 알림

사용자는 한 번의 자연어 질의로 4개 영역의 답변을 통합 대시보드 형태로 받게 됩니다.

---

## Q7. 모델 간 데이터 전송 latency 최적화

### 영문 원문
> Since you are using a hybrid of various models (LUXIA, Gemini, GPT), how do you plan to optimize the latency issues that occur during the data transfer process between each model?

### 한글 번역
다양한 모델(LUXIA, Gemini, GPT)을 하이브리드로 사용하므로, 각 모델 간 데이터 전송 과정에서 발생하는 지연 문제를 어떻게 최적화할 계획인가요?

### 질문 의도
사용자 체감 속도, 즉 응답 지연이 너무 크지 않을지에 대한 우려입니다.

### 답변

**먼저 정정해야 할 점**: 모델끼리 직접 통신하지 않습니다. Backend(FastAPI)가 중앙에서 분배하므로, **모델 → 모델 직접 latency는 0**입니다.

**진짜 latency 원인은 (1) 외부 API 응답 시간 + (2) LLM 추론 시간**입니다. 이를 줄이는 4가지 방법:

1. **병렬 호출** (`asyncio.gather`): Q4 답변과 동일하게 독립 Agent를 동시에 실행
2. **스트리밍 응답**: LLM이 답변을 다 만들 때까지 기다리지 않고, 토큰 단위로 흘려서 사용자에게 즉시 표시. Streamlit은 스트리밍을 지원
3. **캐싱**: 자주 반복되는 질의 결과는 저장해두고 재사용
4. **모델 선택 최적화**: Gemini Flash는 짧은 작업에는 사용하지 않고 긴 문서 처리에만 사용 (Flash가 단순 질문에는 오히려 느릴 수 있음)

**목표**: P95 응답시간 ≤ 5초로 잡고 측정.

---

## Q8. 사용자 정보 부족 시 추가 입력 요청

### 영문 원문
> When checking eligibility or suitability, how does the system handle cases where it requires more information than what the user initially entered? Does the system automatically trigger a request for the user to input additional information?

### 한글 번역
자격이나 적합성을 확인할 때, 사용자가 처음 입력한 것보다 더 많은 정보가 필요한 경우 시스템은 어떻게 처리하나요? 시스템이 자동으로 사용자에게 추가 정보 입력을 요청하나요?

### 질문 의도
UX의 자연스러움, 즉 정보 부족 상황에서 시스템이 어떻게 대응하는지에 대한 질문입니다.

### 답변
**Slot-filling 패턴**을 도입합니다.

1. **필수 슬롯 점검**: 각 Agent가 작동 전 자신에게 필요한 정보를 점검합니다. 예) Policy Agent는 [나이, 거주지, 소득]이 필요
2. **클라리피케이션 질문**: 누락된 슬롯이 있으면 답변 대신 추가 질문을 반환합니다. 예) "거주지를 알려주시면 더 정확한 정책을 찾아드릴게요"
3. **프로필 누적**: 사용자가 답하면 그 정보를 프로필에 누적 저장합니다. 다음 질의부터는 다시 묻지 않습니다.
4. **Structured Output**: LLM의 structured output 기능(JSON 형식 강제)을 활용해 어떤 슬롯이 비었는지 자동으로 판단합니다.

이렇게 하면 사용자가 모든 정보를 미리 채울 필요 없이, 대화 중 자연스럽게 프로필이 완성되어 갑니다.

---

## Q9. 오래된 정보의 데이터베이스 삭제 정책

### 영문 원문
> From the perspective of job seekers, current information is often more important than past data. You mentioned using RAG to update information in real-time; is outdated or insignificant past information eventually deleted from the database?

### 한글 번역
구직자 관점에서는 과거 데이터보다 현재 정보가 더 중요한 경우가 많습니다. RAG로 정보를 실시간 업데이트한다고 하셨는데, 시간이 지나 무의미해진 과거 정보는 결국 데이터베이스에서 삭제되나요?

### 질문 의도
DB가 무한히 비대해지는 것은 아닐지, 그리고 만료된 공고가 추천 결과에 노출되지는 않을지에 대한 우려입니다.

### 답변
**데이터 종류별 수명 정책(TTL: Time-To-Live)**을 설계합니다.

- **채용공고**: 마감일이 지나면 즉시 삭제 또는 "마감됨" 플래그 처리
- **정책 공고**: 마감일 지난 건 메인 검색에서 제외하되, "기록용"으로는 보존 (내년 비슷한 정책 참고용으로 활용 가능)
- **Dynamic RAG로 가져온 사업보고서**: 세션 종료 또는 24시간 후 임시 인덱스 삭제 (메모리 절약)
- **재인덱싱 시 충돌 처리**: 같은 정책ID가 새로 들어오면 **기존 청크 삭제 후 신규 청크 삽입** (upsert 패턴)

이 접근은 단순히 "삭제"가 아니라 **버전 관리 + 만료 정책**의 결합입니다. 데이터의 생애주기를 명확히 정의함으로써 DB 비대화를 막으면서도 필요한 과거 정보는 보존할 수 있습니다.

---

## Q10. Static / Dynamic RAG 사용 사례 예시

### 영문 원문
> I think it's a good idea to divide RAG system into static and dynamic and utilize them for different purpose. Could you briefly give examples about queries and their desired output respectively?

### 한글 번역
RAG 시스템을 static과 dynamic으로 나누어 다른 목적으로 활용하는 것이 좋은 아이디어인 것 같습니다. 각각에 대해 질의와 원하는 출력의 예시를 간단히 들어주실 수 있을까요?

### 질문 의도
두 RAG의 사용 시나리오를 명확히 보여달라는 요청입니다.

### 답변

**Static RAG 예시 (정책 분야)**

- **질의**: "서울 만 25세 무주택 청년이 받을 수 있는 주거지원이 뭐가 있어?"
- **흐름**: 미리 인덱싱된 정책 Vector DB에서 "서울 + 청년 + 무주택 + 주거"의 의미로 검색
- **출력**: "역세권 청년주택", "청년월세지원" 등 미리 저장된 공고문에서 핵심 발췌 + 자격 매칭 결과

**Dynamic RAG 예시 (자소서 분야)**

- **질의**: "삼성전자 DS 부문 지원 자소서 첨삭해줘. 입사 후 포부 부분이야: [텍스트]"
- **흐름**:
  1. MCP로 DART에서 삼성전자 최신 사업보고서 PDF를 가져옴
  2. 그 보고서를 **그 자리에서 청킹·임베딩·임시 Vector DB로 구축**
  3. "DS 부문 신사업, R&D 방향, 인재상" 키워드로 검색
  4. 검색 결과를 LLM 프롬프트에 넣어 자소서 첨삭
- **출력**: "최근 보고서에 따르면 DS 부문은 HBM 메모리 R&D 비중을 늘리고 있습니다. 입사 후 포부에 메모리 미세공정 학습 의지를 반영하면 specificity가 올라갑니다."

**핵심 차이**: Static = 미리 다 만들어둠 / Dynamic = 호출 시점에 만들고 끝나면 버림.

---

## Q11. 자소서가 너무 일반적인 조언이 되지 않게 하는 방법

### 영문 원문
> How will you reduce the risk that the LLM generates overly general advice for the personal statement that could apply to almost anyone rather than providing guidance tailored to a specific company and applicant?

### 한글 번역
LLM이 자소서에 대해 거의 누구에게나 적용 가능한 너무 일반적인 조언만 내놓는 위험을, 특정 회사와 지원자에 맞춘 가이드를 제공하도록 어떻게 줄일 수 있나요?

### 질문 의도
"성실한 사람이 되겠습니다" 같은 누구나 쓸 수 있는 조언이 나올 우려를 어떻게 차단할지에 대한 질문입니다.

### 답변
**Specificity 강제 메커니즘**을 4가지 결합합니다.

1. **회사 specific 데이터 강제 주입**: DART 사업보고서에서 추출한 [신사업, R&D 키워드, 인재상]을 프롬프트에 명시적으로 넣고, "다음 키워드 중 최소 2개를 자연스럽게 활용해 첨삭하라"고 강제
2. **Rubric 기반 채점**: 첨삭 후 LLM-as-judge가 "이 답변이 다른 회사에도 그대로 적용 가능한가?"를 0~5점으로 채점. 3점 이상이면 다시 생성
3. **사용자 경험 강제 결합**: 사용자 프로필의 구체 경험(프로젝트, 자격증, 활동)을 반드시 1개 이상 인용하도록 프롬프트 설계
4. **Few-shot 모범 예시**: 합격 자소서 RAG에서 **같은 회사·같은 직무** 사례를 검색해 예시로 넣음. 그 톤과 구체성을 모방하도록 유도

**평가 메트릭 추가**: "회사명을 다른 회사로 바꿔도 말이 되는가" 테스트 같은 지표를 추가하면 generality를 정량적으로 측정할 수 있습니다.

---

## 📋 마무리: 발표/Q&A 대비 보강 포인트

피드백을 받아 보강할 핵심 3가지를 명확히 정리합니다:

1. **B2 베이스라인 추가** (RAG-only) → 평가 설계 강화 (Q5)
2. **API fallback 4단계 방어선** 명시 → 안정성 강화 (Q3)
3. **Specificity 강제 메커니즘** → 자소서 품질 보강 (Q11)

이 세 가지만 추가해도 다음 발표/응답에서 "피드백을 진지하게 반영했다"는 인상을 줄 수 있습니다.

---

*문서 작성일: 2026-05-09 / Team 10 YouthPath*
