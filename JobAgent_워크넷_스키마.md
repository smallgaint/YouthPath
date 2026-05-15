# Job Agent — 워크넷 API 기반 스키마 (STEP 3-5)

> YouthPath 시스템에서 채용공고를 담당하는 Job Agent의 STEP 3 (입력 수신) → STEP 4 (내부 처리) → STEP 5 (출력 JSON) 까지의 데이터 흐름 및 스키마 명세.
>
> 사람인 API 미보유 → **워크넷 단일 출처**로 동작. 워크넷이 제공하는 5개 엔드포인트를 역할별로 분리해 조합한다.

---

## 0. 보유 API 인벤토리

| # | API | 인증키 (예시) | 승인 일자 | 상태 |
|---|---|---|---|---|
| 1 | 채용정보 | `060d63ed-85c9-4184-bde0-24d4125579ec` | 2026-05-10 | 승인 |
| 2 | 강소기업 | `5cf54e8f-c200-47b8-baf1-cf5a26b80119` | 2026-05-10 | 승인 |
| 3 | 직무정보 | `3de286d2-e3ac-4116-ba47-3d99013f9cde` | 2026-05-10 | 승인 |
| 4 | 공통코드 | `88af74aa-4b74-4eb8-964d-61a8c1194b02` | 2026-05-10 | 승인 |
| 5 | 직업정보 | `62d1a8f5-201f-4210-9839-48c9226d2fdc` | 2026-05-10 | 승인 |

---

## 1. 5개 API의 역할 분리

| API | 호출 빈도 | 캐싱 전략 | 역할 |
|---|---|---|---|
| **채용정보** | 매 질의 (메인) | ❌ 매번 새로 호출 | 공고 후보 가져오기 |
| **공통코드** | 앱 시작 시 1회 | ✅ 메모리 영구 캐싱 | 지역·경력·학력 텍스트 → 코드 룩업 |
| **직업정보** | 앱 시작 시 1회 | ✅ 메모리 영구 캐싱 | 직무명 ↔ 한국직업분류 코드 매핑 |
| **직무정보** | 매 질의 (배치) | ✅ TTL 24h 캐싱 | 직무별 필수/우대 스킬 |
| **강소기업** | 주 1회 갱신 | ✅ 메모리 캐싱 | 회사가 정부 인증 강소기업인지 플래그 |

**분리 원칙**
- 변하지 않는 마스터 데이터(공통코드 / 직업정보 / 강소기업) → 부팅 시 1회 로드, 이후 메모리 룩업만
- 시시각각 변하는 채용 공고(채용정보) → 매번 호출, 캐싱 금지
- 그 중간(직무정보) → TTL 24시간 캐싱

**왜 이렇게 나누나**: 매 질의에서 외부 HTTP 호출은 **딱 1개(채용정보) + 직무정보 배치 1개**까지로 최소화. 나머지는 전부 인메모리 룩업이라 ms 단위로 끝남.

---

## 2. STEP 3 — 분류 LLM의 결정이 Job Agent에 도달

```
[Router의 분류 LLM 출력]
{
  "agents": ["policy", "job", ...],
  "reasoning": "..."
}
        ↓
[LangGraph 그래프가 "job" 노드를 깨움]
        ↓
[Job Agent 입력]
{
  "query":   "서울에서 IT 신입 공고 알려줘",
  "profile": {
    "region":       "서울",
    "target_role":  "데이터 분석가",
    "skills":       ["Python", "SQL"],
    "experience_y": 0,
    "education":    "대졸"
  }
}
```

---

## 3. STEP 4-B — Job Agent 내부 처리 (LLM 호출 없음)

전체 흐름:

```
[입력: query + profile]
        ↓
[A] 텍스트 → 코드 변환 (메모리 캐시 룩업, 외부 API 호출 0번)
        ↓
[B] 채용정보 API 메인 검색 (외부 호출 1번)
        ↓
[C] 강소기업 캐시 룩업 (외부 호출 0번)
        ↓
[D] 직무정보 API 배치 보강 (외부 호출 1번 · 24h 캐시 hit 시 0번)
        ↓
[E] 적합도 점수 계산 (수식, LLM 없음)
        ↓
[F] 정렬 + 상위 K 선택
        ↓
[STEP 5 출력]
```

### 단계별 명세

#### [A] 코드 변환

```python
# 메모리에 이미 로드된 캐시
region_codes = { "서울": "11", "부산": "21", ... }       # 공통코드
career_codes = { "신입": "1", "경력": "2", ... }          # 공통코드
edu_codes    = { "고졸": "00", "전문대": "01", ... }      # 공통코드
job_codes    = { "데이터 분석": "2236",
                 "데이터 분석가": "2236",
                 "데이터분석": "2236", ... }              # 직업정보

# 변환
filters = {
  "regionCd": region_codes[profile.region],       # "11"
  "empTpCd":  career_codes["신입"] if profile.experience_y == 0 else career_codes["경력"],
  "eduLvCd":  edu_codes[profile.education],
  "jobCd":    job_codes[profile.target_role],
}
```

#### [B] 채용정보 메인 검색

```
GET https://www.work.go.kr/openapi/services/rest/JobInfo/getJobInfo
  ?authKey=060d63ed-85c9-4184-bde0-24d4125579ec
  &returnType=json
  &startPage=1
  &display=20
  &regionCd=11
  &jobCd=2236
  &empTpCd=1
  &eduLvCd=00
```

응답 (raw):

```json
{
  "wantedRoot": {
    "wanted": [
      {
        "wantedAuthNo": "K162345789",
        "company":      "○○회사",
        "bizNo":        "123-45-67890",
        "title":        "데이터분석 신입 채용",
        "region":       "서울 강남구",
        "jobsCd":       "2236",
        "career":       "신입",
        "minEdubg":     "대졸",
        "salTpNm":      "연봉",
        "sal":          "3500",
        "regDt":        "2026-05-08",
        "closeDt":      "2026-05-20",
        "infoSvc":      "..."
      },
      ...
    ]
  }
}
```

#### [C] 강소기업 플래그

```python
# 앱 시작 시 강소기업 API로 한 번에 가져와 set으로 캐싱
strong_sme_set: set[str]   # {"123-45-67890", "234-56-78901", ...}  bizno 기준

for job in candidates:
    job.is_strong_sme = job.bizNo in strong_sme_set
```

#### [D] 직무정보 배치 보강

```python
# 후보 공고에서 unique 직무 코드만 추출
unique_codes = {job.jobsCd for job in candidates}    # {"2236", "2231"}

# 캐시 (24h TTL) 우선, miss만 API 호출
skills_map = {}
for code in unique_codes:
    if code in cache_24h:
        skills_map[code] = cache_24h[code]
    else:
        skills_map[code] = fetch_직무정보(code)
        cache_24h[code] = skills_map[code]

# 보강
for job in candidates:
    info = skills_map[job.jobsCd]
    job.required_skills  = info["coreCompetencies"]
    job.preferred_skills = info["prefCompetencies"]
```

#### [E] 적합도 점수 (수식, LLM 없음)

```python
def fit_score(profile, job) -> float:
    s = 0.0
    # 스킬 매칭 (집합 교집합 / 필수스킬 개수)
    if job.required_skills:
        matched = set(profile.skills) & set(job.required_skills)
        s += 0.4 * (len(matched) / len(job.required_skills))
    # 경력 매칭
    s += 0.3 * (1.0 if profile.experience_y_matches(job.career) else 0.0)
    # 지역 매칭 (정확 일치 1.0, 인접 0.5, 그 외 0.0)
    s += 0.2 * region_match(profile.region, job.region)
    # 마감 긴급도 (D-day 짧을수록 1에 가까움)
    s += 0.1 * (1.0 / max(job.days_remaining, 1))
    # 강소기업 가산점
    if job.is_strong_sme:
        s += 0.05
    return min(s, 1.0)
```

#### [F] 정렬 + 상위 K

```python
candidates.sort(key=lambda j: j.fit_score, reverse=True)
top = candidates[:5]
```

---

## 3-1. STEP 4-B 출력 items 키 정의 (UnifiedJob)

[F] 단계의 `top` 리스트 안 각 객체는 다음 22개 키를 갖는 **UnifiedJob** 형태로 정규화되어 [STEP 5]로 넘어간다.

### 컴팩트 키 목록

```json
{
  "wantedAuthNo", "title", "company", "company_bizno", "is_strong_sme",
  "location", "region_code", "job_code",
  "deadline", "days_remaining", "posted_at",
  "career_required", "education_required",
  "salary": { "type", "value", "unit" },
  "required_skills", "preferred_skills",
  "fit_score",
  "fit_breakdown": { "skill", "career", "region", "urgency", "sme_bonus" },
  "source", "url"
}
```

### 키별 타입·필수 여부·기본값

| 키 | 타입 | 필수 | 기본값 | 출처 단계 | 비고 |
|---|---|---|---|---|---|
| `wantedAuthNo` | string | ✅ | — | [B] 채용정보 | 워크넷 공고 고유 ID. dedup 키 |
| `title` | string | ✅ | — | [B] 채용정보 | 공고 제목 (strip 적용) |
| `company` | string | ✅ | — | [B] 채용정보 | 회사명 |
| `company_bizno` | string | ✅ | `""` | [B] 채용정보 | 사업자번호. 강소기업 lookup 키 |
| `is_strong_sme` | bool | ✅ | `false` | [C] 강소기업 캐시 | 정부 인증 강소기업 여부 |
| `location` | string | ✅ | `""` | [B] 채용정보 | 한글 지역명 (`"서울 강남구"`) |
| `region_code` | string | ❌ | `""` | [B] 채용정보 | 표준 지역 코드 (`"11"`) |
| `job_code` | string | ❌ | `""` | [B] 채용정보 | 한국직업분류 코드 (`"2236"`) |
| `deadline` | string (`YYYY-MM-DD`) | ✅ | `""` | [B] 채용정보 | 마감일 |
| `days_remaining` | int | ✅ | `999` | 자체 계산 | `(deadline - today).days`. 파싱 실패 시 999 |
| `posted_at` | string (`YYYY-MM-DD`) | ❌ | `""` | [B] 채용정보 | 공고 등록일 |
| `career_required` | string | ✅ | `""` | [B] 채용정보 | `"신입"` / `"경력"` / `"무관"` 등 |
| `education_required` | string | ❌ | `""` | [B] 채용정보 | `"대졸 이상"` 등 |
| `salary.type` | string | ❌ | `""` | [B] 채용정보 | `"연봉"` / `"월급"` / `"시급"` |
| `salary.value` | int | ❌ | `0` | [B] 채용정보 | 숫자만 (`3500`) |
| `salary.unit` | string | ❌ | `"만원"` | 자체 합성 | 표시용 단위 |
| `required_skills` | string[] | ❌ | `[]` | [D] 직무정보 | 직무별 필수 역량. 직무정보 실패 시 `[]` |
| `preferred_skills` | string[] | ❌ | `[]` | [D] 직무정보 | 직무별 우대 역량 |
| `fit_score` | float (0.0~1.0) | ✅ | `0.0` | [E] 자체 계산 | 최종 적합도 점수 |
| `fit_breakdown.skill` | float | ✅ | `0.0` | [E] 자체 계산 | 0.4 가중치, max 0.4 |
| `fit_breakdown.career` | float | ✅ | `0.0` | [E] 자체 계산 | 0.3 또는 0.0 |
| `fit_breakdown.region` | float | ✅ | `0.0` | [E] 자체 계산 | 0.2 / 0.1 / 0.0 |
| `fit_breakdown.urgency` | float | ✅ | `0.0` | [E] 자체 계산 | `0.1 / max(days, 1)` |
| `fit_breakdown.sme_bonus` | float | ❌ | (생략 가능) | [E] 자체 계산 | 강소기업일 때만 `0.05` 추가 |
| `source` | string | ✅ | `"worknet"` | 자체 합성 | 데이터 소스 식별자. 잡코리아 통과 시 `"jobkorea"` 추가 가능 |
| `url` | string | ✅ | — | 자체 합성 | `wantedAuthNo` 기반 워크넷 상세 페이지 |

### 그룹별 출처 매트릭스 (한눈에)

| 그룹 | 키 | 출처 단계 |
|---|---|---|
| 식별 | `wantedAuthNo`, `title`, `company`, `company_bizno` | [B] 채용정보 |
| 위치·시간 | `location`, `region_code`, `deadline`, `days_remaining`, `posted_at` | [B] 채용정보 + 계산 |
| 자격 | `career_required`, `education_required` | [B] 채용정보 |
| 보상 | `salary` | [B] 채용정보 |
| 직무 보강 | `job_code`, `required_skills`, `preferred_skills` | [B] + [D] 직무정보 |
| 회사 보강 | `is_strong_sme` | [C] 강소기업 (캐시) |
| 점수 | `fit_score`, `fit_breakdown` | [E] 자체 계산 |
| 메타 | `source`, `url` | 자체 합성 |

### 부분 실패 시 키 동작

| 시나리오 | 영향받는 키 | 값 |
|---|---|---|
| 직무정보 API 다운 | `required_skills`, `preferred_skills` | `[]` (빈 배열) |
| 강소기업 캐시 만료 | `is_strong_sme` | `false` |
| deadline 파싱 실패 | `days_remaining` | `999` (정렬 시 자동 후순위) |
| 채용정보 자체 다운 | items 전체 | `[]` + outer `error` 채움 |

→ 모든 케이스에서 **키는 항상 존재**. 값만 기본값/빈 값으로 채움. 클라이언트가 키 존재 여부 체크 없이 안전하게 접근 가능.

---

## 4. STEP 5 — 출력 JSON 스키마

### 공통 외피 (BaseAgent가 강제)

```json
{
  "agent_name": "job",
  "items": [ /* UnifiedJob × 5 */ ],
  "sources": [
    "worknet:채용정보",
    "worknet:직무정보",
    "worknet:강소기업(cached)",
    "worknet:공통코드(cached)",
    "worknet:직업정보(cached)"
  ],
  "metadata": {
    "latency_ms": 450,
    "api_calls": { "채용정보": 1, "직무정보": 1 },
    "cache_hits": { "공통코드": 4, "직업정보": 1, "강소기업": 1 },
    "partial":   false
  },
  "error": null
}
```

### UnifiedJob (items 한 건의 풀 스키마)

```json
{
  "wantedAuthNo":       "K162345789",
  "title":              "데이터분석 신입",
  "company":            "○○회사",
  "company_bizno":      "123-45-67890",
  "is_strong_sme":      true,
  "location":           "서울 강남구",
  "region_code":        "11",
  "job_code":           "2236",
  "deadline":           "2026-05-20",
  "days_remaining":     8,
  "posted_at":          "2026-05-08",
  "career_required":    "신입",
  "education_required": "대졸 이상",
  "salary": {
    "type":  "연봉",
    "value": 3500,
    "unit":  "만원"
  },
  "required_skills":    ["Python", "SQL", "통계 기초"],
  "preferred_skills":   ["Tableau", "추천 시스템"],
  "fit_score":          0.87,
  "fit_breakdown": {
    "skill":     0.36,
    "career":    0.30,
    "region":    0.20,
    "urgency":   0.06,
    "sme_bonus": 0.05
  },
  "source":             "worknet",
  "url":                "https://www.work.go.kr/empSpt/empSrch/empSrchView.do?wantedAuthNo=K162345789"
}
```

### 필드 의미

| 필드 | 출처 | 비고 |
|---|---|---|
| `wantedAuthNo` | 채용정보 | 공고 고유 ID (워크넷) |
| `company_bizno` | 채용정보 | 사업자번호 — 강소기업 lookup 키 |
| `is_strong_sme` | 강소기업 (캐시) | 정부 인증 강소기업 여부 |
| `region_code` | 공통코드 (캐시) | 지역 표준 코드 |
| `job_code` | 직업정보 (캐시) | 한국직업분류 코드 |
| `required_skills` / `preferred_skills` | 직무정보 (24h 캐시) | 직무별 필수·우대 역량 |
| `days_remaining` | 계산 | `(deadline - today).days` |
| `fit_score` / `fit_breakdown` | 자체 계산 | 점수 4 + 가산점 1, 총합 max 1.0 |
| `salary` | 채용정보 | type ∈ {연봉, 월급, 시급}, value 숫자 |
| `url` | 합성 | `wantedAuthNo` 기반 워크넷 상세 페이지 |

---

## 5. 에러·강건성 설계 (단일 출처 보완)

워크넷만 쓰니까 단일 장애점 위험이 큼. 다음 4단으로 방어:

| 계층 | 동작 | 사용자 영향 |
|---|---|---|
| 1. **타임아웃** | 5초 + 지수 백오프 3회 | 응답 지연 |
| 2. **Circuit Breaker** | 연속 5회 실패 시 60초 차단 (호출 자체 안 함) | 빠른 실패 |
| 3. **부분 실패 허용** | 직무정보·강소기업만 죽으면 해당 필드 비우고 `partial: true` 플래그 | 결과는 보이지만 일부 보강 없음 |
| 4. **하드 실패** | 채용정보 자체가 죽으면 빈 items + `error` 필드 채움 | "지금 워크넷이 응답하지 않습니다" 안내 |

### 부분 실패 별 동작

```python
{
  "items": [...],              # 정상 반환
  "metadata": {
    "partial": true,
    "missing": ["직무정보"]    # 어떤 보강이 빠졌는지 명시
  },
  "error": null                # error는 null — 사용자에게 보여줄 결과는 있음
}
```

vs 하드 실패:

```python
{
  "items": [],
  "metadata": { "partial": false },
  "error": {
    "code":    "WORKNET_EMPLOY_UNAVAILABLE",
    "message": "워크넷 채용정보 API가 일시적으로 응답하지 않습니다"
  }
}
```

---

## 6. 부팅 시 (앱 시작) 시퀀스

```
FastAPI startup
   ↓
① 공통코드 API 호출 1회
   → region_codes, career_codes, edu_codes 메모리 적재
   ↓
② 직업정보 API 호출 1회 (페이지네이션으로 전체)
   → job_codes 메모리 적재 (~수천 건)
   ↓
③ 강소기업 API 호출 1회
   → strong_sme_set 메모리 적재 (~수만 건)
   ↓
[ 매주 일요일 새벽 4시 cron으로 ②③ 재로드 ]
   ↓
서버 ready — 이후 매 질의는 채용정보 1번 + 직무정보 (캐시 miss 시) 1번만 호출
```

---

## 7. 문서 (프로젝트_동작_프로세스.md) 정정 항목

지금 메인 문서 STEP 4-B에는 사람인이 같이 들어가 있음 → 다음 4곳을 사람인 제거 + 워크넷 5종으로 수정 필요:

1. **STEP 4-B 1번** "Worknet + Saramin API를 asyncio.gather로 동시 호출" → "워크넷 채용정보 API 호출 + 4개 보조 API(공통코드·직업정보·직무정보·강소기업) 캐시 룩업"
2. **STEP 4-B 2번** "두 API 응답을 UnifiedJob 형식으로 통일" → "채용정보 응답을 UnifiedJob으로 정규화하고 보조 API로 enrich"
3. **STEP 4-B 3번** "중복 제거" → 단일 출처라 회사+직무 dedup만 (다른 소스 없음)
4. **STEP 4-B API 실패 대응** "일부 API만 실패하면 다른 결과로 응답" → 본 문서 §5의 4단 방어 구조로 교체

---

## 8. 한 장 요약

```
입력: query + profile
   ↓
① 텍스트→코드 변환 (3개 캐시 룩업, 0 HTTP)
   ↓
② 채용정보 API 1회 (메인, 1 HTTP)
   ↓
③ 강소기업 캐시 룩업 (0 HTTP)
   ↓
④ 직무정보 배치 보강 (캐시 miss만, 0-1 HTTP)
   ↓
⑤ 적합도 점수 계산 (수식)
   ↓
⑥ 정렬 + 상위 5
   ↓
출력: UnifiedJob × 5 (외피 + items + sources + metadata)
```

**총 HTTP 호출**: 1~2회 / 질의. LLM 호출: 0회.
