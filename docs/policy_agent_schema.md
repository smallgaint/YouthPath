# Policy Agent 응답 스키마 (W12)

YouthPath Policy Agent의 **최종 출력 형식** 정의. `B_프로젝트_동작_프로세스.pdf`의 STEP4(각 Agent의 응답 JSON 형식)를 Policy 도메인에 맞게 구체화한 문서.

- 기계 검증용 스키마: [`policy_agent_response.schema.json`](policy_agent_response.schema.json) (JSON Schema draft 2020-12)
- 현재 구현 상태: [`w11_policy_status.md`](w11_policy_status.md), [`policy_flow_diagrams.md`](policy_flow_diagrams.md)

---

## 1. 범위 및 설계 원칙

- **공통 외피**(`agent_name` / `items` / `sources` / `metadata` / `error`)는 4개 Agent가 공유. Router가 어떤 Agent든 같은 방식으로 다루기 위함. 이 부분은 PDF 정의를 그대로 따른다.
- **`items` 내부 키**는 Policy 도메인 전용. 정책의 핵심은 "자격 충족 조건"이므로 `matched_criteria` / `unmatched_criteria`를 중심으로 설계한다.
- **출력엔 의미 있는 정보를 모두 담되, 형태는 정의된 채로.** 자유형 `extra` blob은 두지 않는다 — 포맷터·카드·통합 LLM이 키를 모르면 못 쓰고, PDF의 "JSON→자연어 변환" / "위에 없는 정보 금지" 원칙과 충돌한다. 대신 빠진 정보는 정식 필드로 승격하고, 그래도 더 필요하면 다운스트림이 **별도로 요청**한다.
- 정규화 전 원본은 `normalize_policy()`의 `raw`에 통째로 보존되므로 "만약의 상황" 안전망은 service 레이어에 이미 있다. Agent 출력에 `raw`를 싣지 않는다(토큰 낭비).
- 현재 `services/policy_service.py`의 `policy_search()`는 `{candidates, chunks, matched}`라는 **중간 산출물**을 반환한다. 이 문서의 스키마는 그 위에 올릴 **표준 Agent 출력**이며, W12에서 `build_policy_response()`로 구현 예정.

---

## 2. 응답 전체 구조 (공통 외피)

```jsonc
{
  "agent_name": "policy",
  "items": [ /* policyItem 배열, score 내림차순 */ ],
  "sources": ["온통청년 getPlcy API", "Chroma policies"],
  "metadata": { /* 아래 6절 */ },
  "error": null
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `agent_name` | `"policy"` 고정 | Router가 포맷터를 선택하는 키 |
| `items` | `policyItem[]` | score 임계값 통과 정책. **score 내림차순 정렬** |
| `sources` | `string[]` | 이번 응답에 **실제 사용된** 소스만. API 실패 시 `["Chroma policies"]`만 |
| `metadata` | `object` | 실행 정보·데이터 품질 신호 |
| `error` | `string \| null` | 정상이면 `null`. 부분 실패 시 사람이 읽을 메시지 |

> **부분 실패 원칙**: API가 죽어도 RAG 결과만으로 `items`를 채우고, `error`에 `"API timeout, RAG-only 결과"`처럼 남긴다. 빈 배열로 죽지 않는다.

### 2-1. 전체 구조 한눈에 보기 (모든 필드 주석)

아래는 **모든 필드를 한 번에** 보여주는 주석 달린 예시다. 질의 `"서울 청년 주거 지원"`, 프로필 `{age: 27, region: "서울"}`(소득 미입력)로 `울릉섬 청년 주거비 지원사업`이 후보로 잡힌 경우. 각 필드 정의는 3절 이하 참고.

```jsonc
{
  "agent_name": "policy",                       // 고정값. Router가 포맷터 고르는 키
  "items": [                                    // score >= 0.6 통과 정책, score 내림차순
    {
      // ── 식별·표시 ──
      "policy_id": "20260409005400212660",       // 정책 고유 ID. dedup·Calendar 흡수·카드 key
      "title": "울릉섬 청년 주거비 지원사업",        // 정책명 (HTML 태그 제거)
      "summary": "19~49세 무주택 1인가구 청년에게 월 최대 20만원, 1년 지원",  // 카드 본문용 1~2문장
      "benefit": "1년 지원, 월 최대 20만원(신혼부부 30만원) 지급. 미지급분 소급 정산",  // 지원 내용(얼마/무엇)
      "region_label": "경상북도 울릉군",            // 사람이 읽는 지역명 (코드→한글 변환 결과)
      "category": "주거",                         // 대분류로 통일
      "keywords": ["주거지원"],                    // plcyKywdNm 콤마 분리
      "host_org": "경상북도 울릉군 미래전략과",       // 소관 기관

      // ── 마감 ──
      "deadline": "2026-04-30",                  // ISO-8601. 상시·미정·파싱실패는 null
      "deadline_type": "마감일",                   // "마감일" | "상시" | "미정"
      "deadline_raw": "20260413 ~ 20260430",      // 원본 보존 (디버깅·검증용)

      // ── 점수·자격 매칭 ──
      "score": 0.65,                             // 0~1. age(0.4)+region(0.3)+income(0.3)
      "matched_criteria": [                      // 프로필로 판정 가능 + 충족
        { "label": "나이", "required": "19~49세", "user_value": "27세", "ok": true }
      ],
      "unmatched_criteria": [                    // 판정 가능하나 미충족 / 프로필 없어 확인불가
        { "label": "지역", "required": "경상북도 울릉군", "user_value": "서울", "ok": false },
        { "label": "소득", "required": "중위소득 150% 이하", "user_value": "미입력", "ok": false }
      ],
      "other_conditions": [                      // 정책 조건이지만 현재 판정 안 함 (ok 없음)
        { "label": "결혼상태", "required": "제한없음" },
        { "label": "기타", "required": "울릉군에 2025.07.01. 이전 전입신고한 1인 가구 무주택 청년" }
      ],

      // ── 신청·링크·추적 ──
      "apply_method": "읍·면 방문 신청",            // 신청 방법 → "구체적 다음 단계" 안내
      "exclusion": "타 주거지원 사업 수혜 중인 자, 주택 소유자, 임대인이 가족인 경우",  // 신청 제외 대상. 없으면 null
      "link": "https://www.ulleung.go.kr/ko/page.do?mnu_uid=571",  // 신청/안내 URL. 없으면 null
      "source": "api+rag"                        // "api" | "rag" | "api+rag"
    }
  ],
  "sources": ["온통청년 getPlcy API", "Chroma policies"],  // 실제 사용한 소스만
  "metadata": {
    "latency_ms": 412,                           // Agent 실행 시간(ms)
    "query": "서울 청년 주거 지원",                 // 실제 사용한 검색 질의
    "candidate_count": 10,                       // 점수 필터 이전 후보 수
    "matched_count": 1,                          // items에 포함된 수
    "api_path": "official",                      // official|legacy|portal|none
    "region_unresolved": 3                       // 지역 코드 변환 실패 건수 (데이터 품질 신호)
  },
  "error": null                                  // 정상이면 null, 부분 실패 시 메시지
}
```

---

## 3. `policyItem` 스키마

### 3-1. 식별·표시 필드

| 필드 | 타입 | 출처 (raw 필드) | 설명 |
|---|---|---|---|
| `policy_id` | `string` | `plcyNo` / `DOCID` | 정책 고유 ID. dedup·Calendar 흡수·카드 key |
| `title` | `string` | `plcyNm` / `PLCY_NM` | 정책명. HTML 태그 제거 |
| `summary` | `string` | `plcyExplnCn` / `PLCY_EXPLN_CN` | 카드 본문용 1~2문장. 정제 후 첫 80자 내외 |
| `benefit` | `string` | `plcySprtCn` / `PLCY_SPRT_CN` | **지원 내용(얼마/무엇)** — 결정의 1순위. 비었으면 `""` |
| `region_label` | `string` | `region` (가공) | 사람이 읽는 지역명. 5절 변환 규칙 참고 |
| `category` | `string` | `lclsfNm` / `USER_CLSF_NM` | **대분류로 통일** (주거/일자리/복지문화/교육/참여권리) |
| `keywords` | `string[]` | `plcyKywdNm` | 콤마 분리, HTML 태그 제거. 카드 태그·필터용 |
| `host_org` | `string` | `sprvsnInstCdNm` | 소관/주관 기관. 신뢰도·문의처 |

### 3-2. 마감 필드

| 필드 | 타입 | 출처 | 설명 |
|---|---|---|---|
| `deadline` | `string \| null` | `aplyYmd` / `APLY_PRD_END_YMD` | ISO-8601(`YYYY-MM-DD`). 상시·미정·파싱 실패는 `null` |
| `deadline_type` | `"마감일" \| "상시" \| "미정"` | `APLY_PRD_SE_CD` | 마감 성격 구분 |
| `deadline_raw` | `string` | `aplyYmd` 등 원본 | 원본 보존(디버깅·검증용) |

### 3-3. 점수·자격 매칭 필드

| 필드 | 타입 | 출처 | 설명 |
|---|---|---|---|
| `score` | `number` (0~1) | 계산 | 자격 적합도. 7절 |
| `matched_criteria` | `criterion[]` | 계산 | 프로필로 판정 가능했고 **충족**한 조건 |
| `unmatched_criteria` | `criterion[]` | 계산 | 판정 가능했으나 **미충족**, 또는 프로필 값이 없어 **확인 불가**한 조건 |
| `other_conditions` | `otherCondition[]` | `mrgSttsNm`, `qlfcAcbgNm`, `empmSttsNm`, `mjrCndNm`, `spclFldNm`, `addAplyQlfcCndCn` | 정책이 요구하지만 **현재 프로필로 판정하지 않는** 조건. 점수 미반영, 카드·통합 LLM 참고용 |

### 3-4. 신청·링크·추적 필드

| 필드 | 타입 | 출처 | 설명 |
|---|---|---|---|
| `apply_method` | `string` | `plcyAplyMthdCn` | 신청 방법. "구체적 다음 단계" 안내에 직결 |
| `exclusion` | `string \| null` | `ptcpPrpTrgtCn` | 신청 제외 대상. 자격이 있어도 탈락시키는 조건. 없으면 `null` |
| `link` | `string \| null` | `aplyUrlAddr` → `refUrlAddr1` → RAG `source_url` | 신청/안내 URL |
| `source` | `"api" \| "rag" \| "api+rag"` | 계산 | 이 정책이 나온 경로 |

### 3-5. `criterion` (프로필로 판정한 자격 조건 1건)

```jsonc
{ "label": "나이", "required": "19~49세", "user_value": "27세", "ok": true }
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `label` | enum | `나이` `지역` `소득` `학력` `취업상태` `결혼상태` `전공` `특화분야` `주택소유` — 입력 프로필 확장 시 항목 추가 |
| `required` | `string` | 정책이 요구하는 값 |
| `user_value` | `string` | 사용자 프로필 값. 미입력 시 `"미입력"` |
| `ok` | `boolean` | `true`=충족, `false`=미충족 또는 확인 불가 |

### 3-6. `otherCondition` (판정하지 않는 조건 1건)

```jsonc
{ "label": "결혼상태", "required": "미혼" }
```

`criterion`과의 차이는 **`ok` 판정이 없다**는 것. 정책엔 조건이 있지만 현재 입력 프로필로는 비교하지 않는 항목이다. 입력 프로필이 다양해지면 일부 `other_conditions` 항목은 `matched/unmatched_criteria`로 승격된다.

| 필드 | 타입 | 설명 |
|---|---|---|
| `label` | `string` | 코드 필드 기반(`결혼상태`/`학력`/`취업상태`/`전공`/`특화분야`) 또는 자유 문구는 `"기타"` |
| `required` | `string` | 정책이 요구하는 값 (예: `"미혼"`, `"(예비)창업자"`, `"무주택 청년"`) |

> **이모지·✓·배지·문장은 데이터에 넣지 않는다.** PDF 예시의 `"나이 27세 ✓"`처럼 표현을 데이터에 박으면 카드 렌더러가 색·아이콘을 못 입히고 포맷터도 재파싱해야 한다. 데이터는 구조만 주고, 표현은 포맷터와 카드가 담당한다.

---

## 4. 텍스트 필드 정제 규칙

`summary` · `benefit` · `apply_method` · `exclusion` · `keywords` · `host_org`는 raw에서 가져올 때 다음을 공통 적용한다 (`scripts/index_policies.py`의 `_clean_text`와 동일 규칙):

- `<span class="highlight">...</span>` → 내부 텍스트만 남김
- 그 외 HTML 태그 제거
- `\xa0` → 공백, 연속 공백·탭 1칸으로
- 데이터에 섞인 기호(`⃞`, `〇` 등) 제거 또는 공백 처리
- 줄바꿈 3개 이상 → 2개로
- `keywords`는 위 정제 후 `,`로 split, 빈 항목 제거
- `other_conditions`는 `"제한없음"` / 빈값이면 항목에서 제외 (`mrgSttsNm`은 `"제한없음|기혼|미혼"`처럼 `|` 구분이므로 split 후 `"제한없음"` 포함 시 스킵)

---

## 5. 원본 데이터 이슈와 정규화 규칙

`data/policies/*.json`과 `data/api_samples/`를 점검한 결과, `normalize_policy()` 출력에 **그대로 쓰면 안 되는 값**이 섞여 있다. Agent 출력으로 올리기 전 반드시 정규화한다.

### 5-1. `region` — 포맷 2종 혼재 (가장 시급)

| 정책 | `region` 실제 값 | 형태 |
|---|---|---|
| 울릉섬 청년 주거비 지원사업 | `"47940"` | 법정동 코드 |
| 청년 주거급여 분리지급 | `"29110,29140,29155,..."` | 코드 CSV |
| 학자금대출 장기연체자 지원 | `"경기도 군포시"` | 한글명 |
| 그린스타트업타운 운영 | `"충청남도 천안시,충청남도 공주시,..."` | 한글명 CSV |

문제: `_region_matches()`의 `_normalize_region()`은 한글을 가정한다. 코드값 `"47940"`이 오면 `"서울"`과 **절대 매칭되지 않고 조용히 실패**한다.

**규칙**:
- `region`이 숫자/숫자CSV → 앞 2자리로 시도 매핑 (`11`=서울, `26`=부산, `27`=대구, `28`=인천, `29`=광주, `30`=대전, `31`=울산, `36`=세종, `41`=경기, `43`=충북, `44`=충남, `46`=전남, `47`=경북, `48`=경남, `42`/`51`=강원, `45`=전북, `50`=제주)
- 한글명이면 그대로 사용
- CSV면 `region_label`은 `"첫 지역 외 N곳"`, 매칭은 항목 중 하나라도 일치하면 `ok`
- 변환 실패 건수는 `metadata.region_unresolved`에 집계

### 5-2. `min_age` / `max_age` — `0/0`이 "제한없음"으로 위장

- 자립준비청년 정책: `min_age=0, max_age=0` → `_age_matches(27, ...)`가 `27 > 0`으로 **거부**. 실제로는 나이무관 정책.
- 그린스타트업: `0 / 99999` (정상 동작)

**규칙**: `raw.SPRT_TRGT_AGE_LMT_YN`을 함께 본다. `0/0` 또는 `0/99999`이고 나이제한 플래그가 무관이면 "나이무관"으로 처리하고 `age_score`는 만점 부여.

### 5-3. `deadline` — 포맷 4종

`"20260413 ~ 20260430"`(범위) · `"20261130"`(단일) · `"0"`(사실은 상시) · `""`(빈값). 게다가 `FIELD_ALIASES["deadline"]`이 `APLY_PRD_SE_CD`를 포함해서 `"상시"`·`"진행중"` 같은 **상태 텍스트**까지 섞여 나온다.

**규칙**:
- 8자리 숫자(`\d{8}`)를 찾아 **마지막 매치**를 마감일로 → `YYYY-MM-DD`
- 숫자 없음 + `APLY_PRD_SE_CD`에 `"상시"` 포함 → `deadline=null`, `deadline_type="상시"`
- 그 외 → `deadline=null`, `deadline_type="미정"`
- 원본은 항상 `deadline_raw`에 보존
- 이렇게 정규화해야 Calendar Agent의 `extract_deadline()`이 안전하게 흡수 가능

### 5-4. `income` — 사실상 빈 필드

정규화된 `income`은 `"0"` / `""` / `"별도 선정기준에 따름"`이라 매칭 불가. 진짜 정보는 `raw.EARN_ETC_CN`에 자연어로 있다: `"중위소득 150%이하"`, `"기준중위소득 48% 이하"`, `"2026년 기준중위소득 60%~160% 이하인 자"`.

**규칙**: `raw.EARN_ETC_CN`에서 `중위소득\s*~?\s*(\d+)\s*%` 정규식으로 상한 %를 추출. 사용자 분위 ≤ 상한이면 `ok`. 추출 실패 시 "확인 불가"로 `unmatched_criteria`에 넣되 `income_score`는 0이 아닌 부분점수(7절).

### 5-5. `category` — 포맷 2종

`"전월세 및 주거급여 지원"`(중분류) vs `"금융・복지・문화_취약계층 및 금융지원"`(대분류_중분류). **대분류만 취해** 통일한다 (`lclsfNm` 또는 `USER_CLSF_NM`).

### 5-6. `link` — 절반이 빈 문자열

`normalize_policy`는 `APLY_URL_ADDR → REF_URL_ADDR1` 순, `index_policies.py`는 반대 순으로 우선순위가 어긋나 있다. **통일**: `aplyUrlAddr` → `refUrlAddr1` → RAG 청크 metadata의 `source_url` → `null`.

---

## 6. `metadata` 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `latency_ms` | `integer` | Agent 실행 시간(ms) |
| `query` | `string` | Agent가 실제 사용한 검색 질의 |
| `candidate_count` | `integer` | 점수 필터 이전 후보 정책 수 |
| `matched_count` | `integer` | `items`에 포함된 수 |
| `api_path` | `"official" \| "legacy" \| "portal" \| "none"` | `ontong_api` 3단 fallback 중 응답 경로. 평가 탭·디버깅용 |
| `region_unresolved` | `integer` | 지역 코드 변환 실패 건수. 데이터 품질 신호 |

---

## 7. score 계산 규칙

PDF의 `0.4 / 0.3 / 0.3` 가중치를 따르되, **데이터 누락을 0점이 아닌 부분점수**로 둔다. 안 그러면 region 코드 정책(샘플의 절반)이 전부 컷된다.

```text
age_score    = 0.4   나이 범위 안 OR 나이무관 정책
             = 0.0   범위 밖

region_score = 0.3   지역 일치 OR "전국"
             = 0.15  region 코드 변환 실패 (불확실 → 중간점수)
             = 0.0   명확히 불일치

income_score = 0.3   사용자 분위 ≤ 정책 상한
             = 0.15  EARN_ETC_CN에서 % 추출 실패 (정보 없음)
             = 0.0   초과

score = age_score + region_score + income_score
items 포함 조건: score >= 0.6
```

> **입력 프로필 확장 시**: 학력·취업상태·결혼상태 등 새 매칭 항목이 들어오면 현재 3항목 고정 가중치는 깨진다. 그때는 (a) 판정 가능한 항목들에 가중치를 정규화 분배하거나 (b) `matched / (matched + unmatched)` 비율 기반으로 재설계한다. 그 전까지 판정 안 하는 조건은 `other_conditions`로만 노출한다.

---

## 8. 전체 예시 응답 (복사용, 주석 없음)

2-1절과 동일한 케이스의 **순수 JSON** 버전. 그대로 파싱·테스트에 쓸 수 있다.

```json
{
  "agent_name": "policy",
  "items": [
    {
      "policy_id": "20260409005400212660",
      "title": "울릉섬 청년 주거비 지원사업",
      "summary": "19~49세 무주택 1인가구 청년에게 월 최대 20만원, 1년 지원",
      "benefit": "1년 지원, 월 최대 20만원(신혼부부 30만원) 지급. 계약 시점에 따라 미지급분 소급 정산",
      "region_label": "경상북도 울릉군",
      "category": "주거",
      "keywords": ["주거지원"],
      "host_org": "경상북도 울릉군 미래전략과",
      "deadline": "2026-04-30",
      "deadline_type": "마감일",
      "deadline_raw": "20260413 ~ 20260430",
      "score": 0.65,
      "matched_criteria": [
        { "label": "나이", "required": "19~49세", "user_value": "27세", "ok": true }
      ],
      "unmatched_criteria": [
        { "label": "지역", "required": "경상북도 울릉군", "user_value": "서울", "ok": false },
        { "label": "소득", "required": "중위소득 150% 이하", "user_value": "미입력", "ok": false }
      ],
      "other_conditions": [
        { "label": "결혼상태", "required": "제한없음" },
        { "label": "기타", "required": "울릉군에 2025.07.01. 이전 전입신고한 1인 가구 무주택 청년" }
      ],
      "apply_method": "읍·면 방문 신청",
      "exclusion": "타 주거지원 사업 수혜 중인 자, 주택 소유자, 임대인이 가족인 경우",
      "link": "https://www.ulleung.go.kr/ko/page.do?mnu_uid=571",
      "source": "api+rag"
    }
  ],
  "sources": ["온통청년 getPlcy API", "Chroma policies"],
  "metadata": {
    "latency_ms": 412,
    "query": "서울 청년 주거 지원",
    "candidate_count": 10,
    "matched_count": 1,
    "api_path": "official",
    "region_unresolved": 3
  },
  "error": null
}
```

---

## 9. 미해결 / TODO (W12)

- [ ] 법정동 코드 → 시도명 매핑 테이블 작성 (`region` 버그가 최우선)
- [ ] `normalize_policy()`에 `deadline` ISO 정규화 + `deadline_type` 분리 추가
- [ ] `EARN_ETC_CN` 소득 % 추출기 + 소득 매칭 룰
- [ ] `_is_profile_match`(불리언)를 가중 `score` 계산으로 교체
- [ ] `benefit` / `apply_method` / `exclusion` / `keywords` / `host_org` / `other_conditions` 추출기 (`_clean_text` 규칙 공유)
- [ ] `build_policy_response(profile, query)` 구현 — `candidates`+`chunks`+`matched`를 join해 위 스키마로 변환
- [ ] `policy_id` 기준 유사 정책 dedup (예: "청년 주거급여 분리지급" / "미혼청년 주거급여 분리지급")
- [ ] 스키마 검증 테스트 추가 (`jsonschema`로 `build_policy_response` 출력 검증)
- [ ] 입력 프로필 확장 확정 후 score 가중치 재설계 + `other_conditions` → `criterion` 승격
