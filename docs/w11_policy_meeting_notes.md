# W11 팀원 A 회의 준비 메모

## 5/12까지 완료할 데모

- 온통청년 공식 `getPlcy` API에서 정책 후보를 가져온다.
- `data/policies/`에 정책 JSON을 50개 이상 저장한다.
- `scripts/index_policies.py`로 `policies` Chroma 컬렉션을 만든다.
- `services.policy_service.policy_search(profile, query)`가 raw dict를 반환한다.

## 데모 쿼리

```text
서울 청년 주거 지원
```

예시 프로필:

```python
{"age": 24, "region": "서울", "income_bracket": "중위 100% 이하"}
```

## 회의에서 합의할 질문

- D가 정할 `Profile` 필드명은 `age`, `region`, `income_bracket`으로 가도 되는가?
- `AgentResponse.items`에 정책 미달 사유를 넣는 필드명을 `unmatched_criteria`로 고정할 것인가?
- C의 회사 RAG도 `core/rag.py`의 `index_documents/search` 인터페이스를 그대로 쓰는가?
- EC2 배포 때 `chroma_data/`를 이미지에 포함할지, 배포 후 재인덱싱할지 E와 결정이 필요하다.

## 현재 결정

- 청킹 기본값은 문서 권장안인 `1000자 + 100자 overlap`.
- W11의 `policy_search()`는 요약/그룹핑 없이 `candidates`, `chunks`, `matched`만 반환한다.
- 공식 API는 `go/ythip/getPlcy` + `apiKeyNm` 방식으로 성공 확인했다.
