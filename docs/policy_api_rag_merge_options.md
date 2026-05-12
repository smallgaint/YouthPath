# API와 RAG 결합 방안 검토

## 확인한 구현 가능성

| 확인 항목 | 결과 |
|---|---|
| 공식 API 키 기반 호출 | 가능 |
| 공식 API 정책명 검색 `plcyNm` | 가능하지만 표현에 민감 |
| 공식 API 정책 ID 단건 조회 `plcyNo` | 가능 |
| 공식 API 키워드 검색 `plcyKywdNm` | 가능 |
| 공식 API 대분류 검색 `lclsfNm` | 가능 |
| Chroma `policy_id` metadata filter | 가능 |
| API 후보와 RAG 후보 `policy_id` 병합 | 가능 |

## 쿼리별 API/RAG overlap 확인

| 쿼리 | API 후보 | RAG 후보 | overlap | 해석 |
|---|---:|---:|---:|---|
| 서울 청년 주거 지원 | 4 | 10 | 0 | API와 RAG가 다른 후보를 냄. 둘 다 살릴 필요 있음 |
| 30살 이하 창업 지원금 | 0 | 10 | 0 | API 정책명 검색이 표현을 놓침. RAG가 필요함 |
| 대학생 학자금 대출 | 5 | 10 | 4 | API/RAG가 잘 맞는 경우도 있음 |

## 방안 A: API First + RAG 보강

```text
API 후보 검색 → 후보 policy_id 확보 → RAG 청크 검색 → 같은 policy_id 청크를 evidence로 연결
```

장점:

- 최신 정책 상태와 구조화 필드를 API에서 얻는다.
- RAG는 상세 근거 청크 역할을 한다.

한계:

- API 검색이 못 잡은 후보는 누락될 수 있다.

## 방안 B: RAG First + API 상세 확인

```text
RAG top-k 검색 → policy_id 추출 → API plcyNo 단건 조회 → 최신 상세 정보 확인
```

장점:

- 자연어 질문에 강하다.
- `"30살 이하 창업 지원금"`처럼 API 정책명 검색이 놓친 경우에도 후보를 찾는다.

한계:

- 벡터 DB가 오래되면 최신 정책 누락 가능성이 있다.

## 방안 C: Hybrid Merge + 점수화

```text
API top-N + RAG top-K union → policy_id 기준 병합 → API/RAG/자격 점수 합산
```

점수 예시:

```text
API 후보 포함: +0.25
RAG top-k 포함: +0.35
나이 조건 일치: +0.15
지역 조건 일치: +0.15
소득 조건 일치: +0.10
```

장점:

- API와 RAG 중 하나가 놓친 정책도 살릴 수 있다.
- W13 평가에서 튜닝하기 좋다.

한계:

- W11 raw 반환 원칙보다 복잡하므로 W12 Agent 단계에 적합하다.

## 방안 D: API 후보 필터 후 Vector Search

```text
API에서 조건 후보 축소 → Chroma metadata filter → 제한된 후보 안에서 벡터 검색
```

장점:

- 자격 조건과 의미 검색을 동시에 반영할 수 있다.

한계:

- 지역/소득 메타데이터 정규화가 필요하다.
- 후보를 너무 좁히면 RAG 장점이 줄어든다.

## 추천 결론

W12에서는 **B안 + C안 조합**을 추천한다.

```text
1. RAG top-k에서 policy_id 추출
2. API plcyNo 단건 조회로 최신 상세 확인
3. API query 후보도 별도 조회
4. 두 후보군을 union
5. profile 기반 룰 점수화
6. AgentResponse.items에 matched/unmatched criteria 포함
```

이 방식이 API의 최신성과 RAG의 자연어 검색 장점을 가장 균형 있게 가져간다.
