# 팀원 A 5분 발표안

## 1. 역할

저는 정책 도메인과 Static RAG 인프라를 맡았습니다. 목표는 온통청년 정책 데이터를 수집하고, Chroma `policies` 컬렉션에 인덱싱해서 Policy Agent가 LLM 없이 정책 후보와 근거 청크를 가져오게 하는 것입니다.

## 2. 구현한 것

- `clients/ontong_api.py`: 온통청년 공식 `getPlcy` API 호출, JSON/XML 파싱, 정책 필드 정규화
- `scripts/collect_policies.py`: 정책 50개 이상 수집 스크립트
- `core/rag.py`: C도 같이 쓸 수 있는 공통 Chroma RAG 헬퍼
- `scripts/index_policies.py`: 정책 JSON을 1000자/100자 overlap으로 청킹 후 인덱싱
- `services/policy_service.py`: `policy_search(profile, query)` 단순 검색 함수

## 3. 데모 흐름

```python
from services.policy_service import policy_search

profile = {"age": 24, "region": "서울", "income_bracket": "중위 100% 이하"}
result = policy_search(profile, "서울 청년 주거 지원")

print(result.keys())  # candidates, chunks, matched
```

## 4. 설계 결정

- W11 단계에서는 결과를 요약하거나 그룹핑하지 않고 raw dict만 반환합니다.
- 청킹은 정책 공고의 자격요건 문단이 잘리지 않도록 `1000자 + 100자 overlap`을 기본값으로 잡았습니다.
- 자격 매칭은 나이와 지역부터 코드 룰로 처리하고, W12에서 소득 조건과 점수화를 확장합니다.
- 공식 API는 `apiKeyNm`, `pageNum`, `pageSize`, `rtnType=json` 파라미터로 호출합니다.

## 5. 회의에서 합의할 내용

- D의 `Profile` 스키마 필드명 확정
- `AgentResponse.items`에 `matched_criteria`, `unmatched_criteria`를 넣을지 확정
- C가 `core/rag.py`를 그대로 사용할 수 있는지 인터페이스 확인
- E와 `chroma_data/` 배포 방식 결정

## 6. API와 RAG 결합 방안

현재 `policy_search()`는 공식 API 후보(`candidates`)와 Chroma 검색 청크(`chunks`)를 나란히 반환한다. W12의 표준 Policy Agent에서는 두 결과를 `policy_id` 기준으로 결합해야 한다.

### 결합안 A: API First + RAG 보강

흐름:

```text
API 후보 검색 → 후보 policy_id 확보 → RAG 청크 검색 → 같은 policy_id 청크를 evidence로 연결
```

확인 결과:

- 공식 API `go/ythip/getPlcy` 호출 성공
- `plcyNo` 단건 조회 가능
- Chroma metadata filter `{policy_id: ...}` 동작 확인

장점:

- 최신 정책과 정확한 구조화 필드를 API에서 가져올 수 있다.
- RAG는 상세 설명과 근거 청크 보강에 집중할 수 있다.

주의:

- API 검색이 정책명 중심이라 쿼리 표현에 민감하다. 예: `"30살 이하 창업 지원금"`은 API 후보 0개였지만 RAG는 창업 정책을 찾았다.

### 결합안 B: RAG First + API 상세 확인

흐름:

```text
RAG top-k 검색 → chunk의 policy_id 추출 → API plcyNo 단건 조회 → 최신 상세 정보 확인
```

확인 결과:

- RAG 결과 metadata에 `policy_id`가 들어 있다.
- 공식 API에서 `plcyNo=정책ID` 단건 조회가 된다.

장점:

- 자연어 질문에 가장 강하다.
- API 검색어가 정확히 맞지 않아도 의미 기반으로 후보를 찾을 수 있다.

주의:

- RAG DB가 오래되면 최신 정책 누락 가능성이 있다.
- 주기적 재수집/재인덱싱이 필요하다.

### 결합안 C: Hybrid Merge + 점수화

흐름:

```text
API top-N + RAG top-K union → policy_id 기준 병합 → API점수/RAG점수/나이/지역/소득 점수 합산
```

확인 결과:

- API 후보와 RAG 후보는 쿼리별로 겹침 정도가 달랐다.
- `"대학생 학자금 대출"`은 API/RAG overlap 4개로 잘 맞았다.
- `"서울 청년 주거 지원"`은 overlap 0개였고, 두 검색원이 서로 다른 후보를 냈다.
- `"30살 이하 창업 지원금"`은 API 후보 0개, RAG 후보 10개였다.

장점:

- API와 RAG 중 하나가 놓친 정책을 살릴 수 있다.
- 평가용 점수화와 설명 가능성이 좋다.

주의:

- W11의 raw 반환 원칙보다는 복잡하므로 W12 Policy Agent에서 구현하는 것이 적절하다.

### 결합안 D: API 후보 필터 후 Vector Search

흐름:

```text
API에서 나이/지역/분류로 후보 축소 → Chroma metadata filter로 후보 안에서 벡터 검색
```

확인 결과:

- Chroma `policy_id` filter는 동작한다.
- 다만 지역 값이 API에서는 코드(`zipCd`)와 명칭(`STDG_NM`)이 섞여 있어 정규화가 필요하다.

장점:

- 자격 조건에 맞는 후보 안에서 의미 검색을 할 수 있어 결과가 안정적이다.

주의:

- API 후보를 너무 좁히면 RAG의 의미 검색 장점이 줄어든다.
- 지역/소득 메타데이터 정규화가 선행되어야 한다.

### W12 추천

1차 구현은 **B안(RAG First + API 상세 확인)** 또는 **C안(Hybrid Merge + 점수화)**가 적합하다. 현재 API 정책명 검색은 표현에 민감하므로, 자연어 질문을 잘 받으려면 RAG 후보를 반드시 살려야 한다.

추천 순서:

```text
1. RAG top-k에서 policy_id 추출
2. API plcyNo 단건 조회로 최신 상세 정보 확인
3. API 후보도 별도로 가져와 union
4. 나이/지역/소득 룰로 점수화
5. AgentResponse.items에 matched_criteria / unmatched_criteria 포함
```
