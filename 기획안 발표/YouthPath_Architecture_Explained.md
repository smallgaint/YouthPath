# YouthPath 시스템 아키텍처 상세 설명

본 문서는 `YouthPath_Architecture.png` 다이어그램의 모든 구성요소를 구체적으로 설명한다.

---

## 1. 다이어그램 개요

YouthPath의 전체 시스템 아키텍처를 4개 레이어로 구성하여 시각화한 다이어그램이다. 좌측에서 우측으로 데이터가 흐르는 구조이며, 각 클러스터는 다음과 같이 색상으로 구분된다.

| 색상 | 클러스터 | 의미 |
|---|---|---|
| 연한 파랑 | AWS Cloud | 전체 인프라 경계 |
| 파랑 | VPC | 네트워크 격리 영역 |
| 주황 | EC2 Application Layer | 애플리케이션 실행 영역 |
| 분홍 | Multi-Agent Orchestration | LangGraph 기반 에이전트 |
| 녹색 | Data Layer | Vector DB 및 메타데이터 저장소 |
| 보라 | External APIs | 외부 데이터 소스 (MCP 서버) |
| 연한 분홍 | LLM Providers | LLM API 제공자 |

---

## 2. 레이어별 상세 설명

### 2.1 사용자 (User)

**위치**: 다이어그램 최좌측

**설명**:
- 만 19~34세 청년 사용자
- 타겟 사용자 약 1,200만 명
- 웹 브라우저를 통해 HTTPS로 시스템에 접근
- 입력 형태: 자연어 질의 (예: "25세 서울 거주, 받을 수 있는 주거 정책?")

**프로토콜**: HTTPS (TLS 1.3)

---

### 2.2 AWS Cloud (전체 인프라 박스)

**역할**: 모든 인프라 컴포넌트를 포함하는 최상위 경계

**선택 이유**:
- 수업에서 AWS Academy 계정 무료 제공
- $50 크레딧 한도 내 운영 가능
- IAM, VPC 등 보안 기능 학습 가능

**제약 조건**: AWS Academy는 EKS, SageMaker 등 일부 서비스 제한. EC2, S3, RDS 위주 활용.

---

### 2.3 Route 53 (DNS)

**역할**: 도메인 이름을 ALB의 IP 주소로 변환

**동작 흐름**:
1. 사용자가 `youthpath.example.com` 입력
2. Route 53이 ALB의 IP 반환
3. 사용자 브라우저가 해당 IP로 HTTPS 연결

**대안**: 도메인 등록이 부담되면 EC2 Public IP로 직접 접근 가능 (개발 단계)

---

### 2.4 ALB (Application Load Balancer)

**역할**: 트래픽을 EC2 인스턴스로 분산

**기능**:
- HTTPS 종료 (TLS 인증서 처리)
- 헬스체크 (EC2 상태 모니터링)
- (확장 시) 여러 EC2 인스턴스 간 부하 분산

**개발 단계 단순화**: 단일 EC2 사용 시 ALB 생략 가능. 운영 단계 도입 권장.

---

### 2.5 VPC (Virtual Private Cloud)

**역할**: AWS 내 격리된 가상 네트워크

**구성**:
- Public Subnet: ALB 배치
- Private Subnet: EC2 (앱 서버), Vector DB, RDS 배치
- Internet Gateway: 외부 통신
- NAT Gateway: Private Subnet에서 외부 API 호출

**보안**: 
- Private Subnet의 EC2는 외부에서 직접 접근 불가
- ALB를 거쳐서만 도달 가능
- 보안 그룹으로 포트 제어 (80, 443, 5432 등)

---

### 2.6 EC2 Application Layer

**역할**: 애플리케이션 코드 실행

**구성**: t3.medium 또는 t3.large 인스턴스 1~2대 (개발 단계)

#### 2.6.1 Streamlit (Frontend)
- **포트**: 8501
- **역할**: 웹 UI 제공
- **주요 페이지**:
  - 사용자 프로필 입력 폼
  - 정책/채용/자소서 통합 대시보드
  - 모의 면접 채팅 인터페이스
  - 답변 평가 결과 차트

#### 2.6.2 FastAPI (Backend)
- **포트**: 8000
- **역할**: REST API 서버
- **주요 엔드포인트**:
  - `POST /query`: 사용자 질의 처리
  - `POST /profile`: 프로필 저장/업데이트
  - `GET /agents/status`: 에이전트 상태 조회
  - `GET /evaluation`: 평가 결과 조회
- **비동기 처리**: async/await로 외부 API 병렬 호출

---

### 2.7 Multi-Agent Orchestration (LangGraph)

**역할**: 여러 에이전트가 협업하여 사용자 질의 처리

**프레임워크**: LangGraph (LangChain 기반 워크플로우 엔진)

**선택 이유**:
- 워크플로우 시각화 용이 (디버깅 강함)
- StateGraph로 상태 관리 명확
- Conditional Edge로 분기 처리
- MCP 통합 지원

#### 2.7.1 Router Agent (LLM ①)
- **담당**: 팀원 D
- **입력**: 사용자 자연어 질의
- **출력**: 호출할 Sub-Agent 목록
- **사용 LLM**: GPT-4o-mini (저비용·정확한 분류)
- **프롬프트 핵심**: "이 질의는 정책/채용/자소서/일정 중 어느 도메인?"
- **분기 로직**: 단일 도메인 → 1개 Agent 호출, 복합 도메인 → 여러 Agent 병렬 호출

#### 2.7.2 Policy Agent
- **담당**: 팀원 A
- **역할**: 사용자 프로필과 청년 정책 자격요건 자동 매칭
- **데이터 소스**: 온통청년 API (MCP) + 정책 공고문 Vector DB (RAG)
- **출력**: 받을 수 있는 정책 목록 + 신청 방법 + 마감일
- **LLM 호출**:
  - LLM ②: 사용자 프로필 구조화 추출
  - LLM ③: 자격 매칭 결과 자연어 생성

#### 2.7.3 Job Agent
- **담당**: 팀원 B
- **역할**: 채용공고 매칭 및 기업 분석
- **데이터 소스**: 워크넷 API + DART API (MCP) + 뉴스 API (MCP)
- **데이터 처리**:
  - 채용공고: 작은 데이터 → Tool Use (그대로 LLM)
  - DART 사업보고서: 큰 데이터 → Dynamic RAG
- **출력**: 적합 채용공고 Top 5 + 기업 인사이트

#### 2.7.4 Resume Agent
- **담당**: 팀원 C
- **역할**: 자소서 첨삭 및 면접 대비
- **데이터 소스**: DART API (MCP) + 합격 자소서 Vector DB (Static RAG)
- **사용 LLM**: LUXIA (한국어 첨삭 자연스러움)
- **출력**: 자소서 수정안 + 모범 답안 + 예상 면접 질문

#### (다이어그램에서 생략된) Calendar Agent
- 마감일 통합 알림 담당
- 다른 Agent 결과에서 마감일을 추출해 RDS에 저장
- 다이어그램 단순화를 위해 생략됨 (실제 구현에는 포함)

---

### 2.8 Data Layer

#### 2.8.1 Chroma (Static RAG)
- **역할**: 사전 인덱싱된 Vector DB
- **저장 데이터**:
  - 청년 정책 공고문 (약 5,000건)
  - NCS 직무 평가 기준 (약 1,000건)
  - 합격 자소서 사례 (약 500건)
- **임베딩 모델**: BAAI/bge-m3 (한국어 우수, 다국어 지원)
- **운영**: EC2 내부 로컬 디렉토리 또는 Docker 컨테이너
- **업데이트 주기**: 주 1회 배치 인덱싱

#### 2.8.2 Chroma (Dynamic RAG)
- **역할**: 런타임에 생성되는 임시 Vector DB
- **저장 데이터**: DART에서 받은 사업보고서 (요청 시마다)
- **수명**: TTL 1시간 (캐시), 이후 자동 삭제
- **메모리 사용**: 회사 1개당 약 50MB (수십 회사 동시 캐싱 가능)

#### 2.8.3 RDS (PostgreSQL)
- **역할**: 관계형 메타데이터 저장
- **저장 데이터**:
  - 사용자 프로필 (나이, 지역, 학력, 관심분야 등)
  - 사용자별 매칭된 정책 이력
  - 신청 마감일 일정 (Calendar Agent용)
  - 시스템 로그 및 평가 데이터
- **인스턴스**: db.t3.micro (개발 단계)
- **백업**: 일 1회 자동 스냅샷

#### 2.8.4 S3 (Object Storage)
- **역할**: 정적 파일 및 백업 저장
- **저장 데이터**:
  - Vector DB 백업 (주 1회)
  - 원본 정책 공고 PDF
  - 사용자 업로드 자소서 파일
  - 평가 결과 리포트
- **버킷 구조**:
  - `youthpath-data/`: 원본 데이터
  - `youthpath-backup/`: 백업
  - `youthpath-uploads/`: 사용자 업로드

---

### 2.9 External APIs (MCP Servers)

각 외부 API를 MCP Server로 래핑하여 표준 프로토콜로 호출.

#### 2.9.1 Youth Center API (온통청년)
- **운영**: 온통청년 (대통령 직속 청년정책추진단)
- **URL**: https://www.youthcenter.go.kr/
- **제공 데이터**: 중앙·지자체 청년 정책 약 8,000건
- **인증**: API 키 (무료 발급)
- **MCP 도구**:
  - `search_youth_policy(keyword, region, age)`: 정책 검색
  - `get_policy_detail(policy_id)`: 정책 상세
  - `check_eligibility(profile, policy_id)`: 자격 매칭

#### 2.9.2 DART OpenAPI (전자공시시스템)
- **운영**: 금융감독원
- **URL**: https://opendart.fss.or.kr/
- **제공 데이터**: 상장기업 공시 (사업보고서, 분기보고서, 주요사항보고서)
- **인증**: API 키 (무료, 일 10,000건 한도)
- **MCP 도구**:
  - `get_corp_code(company_name)`: 회사명 → 고유코드
  - `get_business_report(corp_code, year)`: 사업보고서
  - `get_recent_filings(corp_code, days)`: 최근 공시

#### 2.9.3 Worknet OpenAPI (워크넷)
- **운영**: 한국고용정보원
- **URL**: https://www.work24.go.kr/
- **제공 데이터**: 전국 채용공고 약 30만 건
- **인증**: 공공데이터포털 서비스 키
- **MCP 도구**:
  - `search_jobs(keyword, region, occupation)`: 채용 검색
  - `get_job_detail(job_id)`: 채용 상세

#### 2.9.4 Naver News API
- **운영**: 네이버
- **URL**: https://developers.naver.com/
- **제공 데이터**: 네이버 뉴스 검색 결과
- **인증**: Client ID + Secret (무료 일 25,000건)
- **MCP 도구**:
  - `search_news(query, sort, days)`: 뉴스 검색

---

### 2.10 LLM Providers

전략적으로 3개 LLM을 조합 사용하여 비용과 품질을 최적화.

#### 2.10.1 LUXIA (메인 한국어 LLM)
- **제공**: 수업에서 $50 크레딧 제공
- **URL**: https://platform.luxiacloud.com
- **사용처**:
  - Resume Agent의 자소서 첨삭
  - Policy/Job Agent의 한국어 답변 생성
  - Coach 톤의 친근한 응답
- **선택 이유**: 한국어 도메인 강함, 자연스러운 어투, 수업 자원 활용

#### 2.10.2 GPT-4o-mini (분류·평가용)
- **제공**: OpenAI API
- **가격**: $0.15/1M input, $0.60/1M output
- **사용처**:
  - Router Agent의 도메인 분류
  - LLM-as-judge 답변 평가
  - 사용자 프로필 구조화 추출
- **선택 이유**: 안정적 reasoning, 매우 저렴, JSON 출력 안정

#### 2.10.3 Gemini 2.0 Flash (긴 문서 처리)
- **제공**: Google AI Studio
- **가격**: 무료 (일 1,500요청)
- **사용처**:
  - DART 사업보고서 (수백 페이지) 사전 요약
  - 긴 컨텍스트 통합 분석
- **선택 이유**: 200만 토큰 컨텍스트 윈도우, 무료 tier

---

## 3. 데이터 흐름 시나리오

### 시나리오: 사용자가 "25세 서울 거주, 카카오 IT 직무 지원하려고요. 자소서 도와줘"라고 입력

#### Step 1: 사용자 → 시스템 진입
```
사용자 브라우저 
  → HTTPS 요청 
  → Route 53 (DNS 해석) 
  → ALB (TLS 종료) 
  → EC2 (Streamlit Frontend)
```
**소요 시간**: ~100ms

#### Step 2: Frontend → Backend
```
Streamlit이 사용자 입력 받음
  → FastAPI POST /query 호출
  → JSON: {"user_id": "123", "query": "..."}
```
**소요 시간**: ~50ms

#### Step 3: Router Agent가 의도 분류
```
Router Agent (LLM ① 호출, GPT-4o-mini)
  → 결과: ["job_agent", "resume_agent"]
  → "채용 정보 + 자소서 도움이 필요한 질의"
```
**소요 시간**: ~500ms

#### Step 4: Job Agent + Resume Agent 병렬 실행

**Job Agent**:
```
1. LLM ②: 회사명 "카카오", 직무 "IT" 추출
2. asyncio.gather로 병렬 호출:
   - MCP Worknet: 카카오 IT 채용공고 검색
   - MCP DART: 카카오 사업보고서 받기 (300페이지)
   - MCP Naver News: 카카오 최근 뉴스
3. DART 사업보고서 → Dynamic RAG 처리:
   - 청킹 (500토큰 단위)
   - bge-m3 임베딩
   - 임시 Chroma DB 생성
   - "신사업, 인재상" 검색 → 청크 5개 추출
4. LLM ③: 종합 답변 생성 (LUXIA)
```

**Resume Agent**:
```
1. MCP DART: 카카오 사업보고서 (Job Agent와 캐시 공유)
2. Static RAG 검색:
   - 합격 자소서 DB → "카카오 IT" 관련 5건
   - NCS 평가기준 → "IT 직무" 관련 3건
3. LLM ③: 자소서 첨삭 가이드 생성 (LUXIA)
```

**병렬 실행 효과**: 순차 시 12초 → 병렬 시 4초

#### Step 5: 응답 통합 및 반환
```
LangGraph가 두 Agent 결과 수집
  → FastAPI가 JSON으로 통합
  → Frontend가 받아서 대시보드 렌더링
  → 사용자에게 표시
```

#### Step 6: 부가 작업
```
Calendar Agent가 마감일 추출 → RDS 저장
RDS 일정은 D-7, D-3, D-1에 사용자에게 알림 (이메일/카카오톡)
```

**총 응답 시간**: 약 4~5초 (P95 목표: 5초 이내)

---

## 4. 화살표 및 색상 의미

### 4.1 실선 (Solid Line)
| 색상 | 의미 | 예시 |
|---|---|---|
| 진한 파랑 | 사용자 진입 흐름 (HTTPS) | User → Route 53 → ALB |
| 검정 | 일반 시스템 호출 (REST API) | ALB → Streamlit, FastAPI → Router |
| 빨강 | Router → Sub-Agent 라우팅 | Router → Policy/Job/Resume |
| 보라 | Sub-Agent → 외부 MCP 호출 | Job Agent → DART MCP |

### 4.2 점선 (Dashed Line)
| 색상 | 의미 | 예시 |
|---|---|---|
| 주황 | LLM API 호출 | Sub-Agent → LUXIA/GPT/Gemini |

### 4.3 점점선 (Dotted Line)
| 색상 | 의미 | 예시 |
|---|---|---|
| 회색 | 데이터 백업 | Chroma → S3, RDS → S3 |

---

## 5. 기술 선택 정당화

### 5.1 왜 LangGraph인가?
- **워크플로우 시각화**: 발표 시 그래프 그대로 다이어그램으로 사용 가능
- **상태 관리**: TypedDict 기반 State 명확
- **조건부 분기**: Conditional Edge로 Router 패턴 구현 용이
- **MCP 통합**: 표준 도구 호출 지원

### 5.2 왜 Chroma인가?
- **오픈소스 무료**: $50 크레딧 절약
- **로컬 운영**: AWS RDS 같은 별도 인스턴스 불필요
- **Python 통합 우수**: LangChain과 자연스럽게 연결
- **Pinecone/Weaviate 대비**: 학습 곡선 낮음

### 5.3 왜 bge-m3 임베딩인가?
- **한국어 성능 우수**: 한국어 검색 정확도 0.85+ (MTEB 한국어 벤치마크)
- **다국어 지원**: 한·영·중 동시 처리 (확장성)
- **로컬 실행**: HuggingFace Transformers로 무료 사용
- **Dimension 1024**: 적절한 표현력 + 저장 효율

### 5.4 왜 Multi-LLM 전략인가?
| 작업 특성 | 최적 모델 | 단일 모델로는? |
|---|---|---|
| 한국어 답변 생성 | LUXIA | GPT는 한국어 어투 어색 |
| 분류·평가 (정형) | GPT-4o-mini | LUXIA는 비싸서 낭비 |
| 긴 문서 (200K+) | Gemini Flash | LUXIA/GPT는 컨텍스트 한계 |

→ **모델별 강점 분배로 비용 70% 절감, 품질 동시 확보**

### 5.5 왜 Fine-tuning 대신 RAG인가?
- 정책·공시 데이터는 매주 갱신 → Fine-tuning은 매번 재학습 필요
- RAG는 데이터 추가만으로 즉시 반영
- 출처 인용(citation) 가능 → 신뢰성 ↑
- 학생 환경에서 Fine-tuning은 비용·시간 부담

---

## 6. 확장 가능성 (Future Work)

| 단계 | 추가 컴포넌트 | 다이어그램 변화 |
|---|---|---|
| Phase 2 | CloudFront (CDN) | Route 53 앞단 추가 |
| Phase 2 | ElastiCache (Redis) | Data Layer에 캐시 추가 |
| Phase 3 | Auto Scaling Group | EC2를 ASG로 대체 |
| Phase 3 | Whisper STT | Frontend 옆 음성 입력 |
| Phase 4 | Mobile App | Frontend 분기 (Web + Mobile) |
| Phase 4 | KakaoTalk Bot | External APIs에 추가 |
| Phase 5 | SageMaker Fine-tuning | LLM Provider 옆 추가 |

---

## 7. 보안 고려사항

### 7.1 데이터 보안
- 사용자 프로필 (개인정보)는 RDS 암호화 저장
- API 키는 AWS Secrets Manager 또는 환경변수 (`.env`) 관리
- GitHub에 키 커밋 절대 금지 (`.gitignore` 필수)

### 7.2 네트워크 보안
- Private Subnet의 EC2는 직접 인터넷 접근 차단
- ALB에서만 접근 가능
- 보안 그룹으로 포트 화이트리스트

### 7.3 API 한도 관리
- DART: 일 10,000건 → 캐싱으로 회피
- Worknet: 일 1,000건 → 사용자별 throttling
- Gemini: 일 1,500건 → 도메인별 분배

---

## 8. 비용 분석

### 8.1 개발 단계 (월 비용)
| 항목 | 비용 |
|---|---|
| EC2 t3.medium | $0 (AWS Academy 무료) |
| RDS t3.micro | $0 (AWS Academy 무료) |
| S3 (10GB) | $0.23 |
| LUXIA $50 크레딧 | $0 (수업 제공) |
| GPT-4o-mini (~10만 토큰) | ~$1 |
| Gemini Flash | $0 (무료 tier) |
| **합계** | **약 $1~2/월** |

### 8.2 운영 단계 가정 (월 1,000명 사용자)
| 항목 | 비용 |
|---|---|
| EC2 t3.large × 2 | $120 |
| RDS db.t3.medium | $60 |
| S3 (100GB) | $2.30 |
| ALB | $25 |
| LLM API (총합) | ~$200 |
| **합계** | **약 $400/월** |

---

## 9. 발표 시 활용 포인트

### 9.1 30점 배점 "System Design" 어필
- 4개 레이어 명확한 분리 (관심사의 분리)
- Multi-LLM 전략으로 비용·품질 동시 최적화
- Static + Dynamic RAG hybrid
- MCP 표준 프로토콜 사용 (확장성)

### 9.2 Q&A 대비 예상 질문
- Q: 왜 EKS가 아닌 EC2? → A: AWS Academy 제약 + 학습 비용 대비 효용
- Q: Bedrock 안 쓰는 이유? → A: Academy 미제공 + Multi-LLM 전략 자체 설계
- Q: OpenSearch 대신 Chroma? → A: 비용·운영 단순성, 학생 프로젝트 적합
- Q: 단일 LLM으로 안 되나? → A: 한국어·긴문서·분류 각각 강점 모델 다름

---

## 10. 다이어그램 재생성 방법

다이어그램은 [generate_architecture.py](generate_architecture.py)로 생성된다.

```bash
cd /Users/gimhuiseung/Desktop/딥러닝\ 과제
source .venv/bin/activate
python generate_architecture.py
# → YouthPath_Architecture.png 생성
```

**의존성**:
- graphviz (Homebrew)
- diagrams (pip)

**수정 방법**:
- 노드 추가/제거: Python 코드에서 변수 추가
- 색상 변경: `graph_attr={"bgcolor": "#XXXXXX"}` 수정
- 레이아웃 변경: `direction="LR"` ↔ `"TB"` (좌우/상하)
