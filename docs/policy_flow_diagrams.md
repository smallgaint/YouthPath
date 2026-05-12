# Policy 파트 현재 구현 흐름

## 1. 전체 YouthPath 구조에서 현재 구현된 범위

```mermaid
flowchart TD
    U["사용자 질문"] --> R["Router LLM / D 담당 / 미구현"]
    R --> PA["Policy Agent / W12 표준 Agent / 미구현"]
    R --> JA["Job Agent / B 담당"]
    R --> RA["Resume Agent / C 담당"]
    R --> CA["Calendar Agent / E 담당"]

    PA -. W11 임시 함수로 구현 .-> PS["policy_search(profile, query) / 구현 완료"]
    PS --> API["온통청년 공식 API / go/ythip/getPlcy / 구현 완료"]
    PS --> VDB["Chroma policies Vector DB / 정책 공고문 161개 인덱싱 완료"]
    PS --> RULE["자격 매칭 룰 / 나이, 지역 구현 / 소득은 기초 데이터만 보유"]

    API --> CAND["candidates / API 정책 후보"]
    VDB --> CHUNKS["chunks / 상세 정책 청크"]
    RULE --> MATCHED["matched / 매칭 정책 ID"]

    CAND --> OUT["raw dict 반환 / candidates, chunks, matched"]
    CHUNKS --> OUT
    MATCHED --> OUT

    OUT --> INTEG["통합 LLM 응답 생성 / D 담당 / 미구현"]

    classDef done fill:#d9fbe3,stroke:#16803c,color:#0b3d1c;
    classDef partial fill:#fff4cc,stroke:#a66b00,color:#4d3200;
    classDef todo fill:#f3f4f6,stroke:#6b7280,color:#111827;

    class PS,API,VDB,CAND,CHUNKS,MATCHED,OUT done;
    class RULE,PA partial;
    class R,JA,RA,CA,INTEG todo;
```

## 2. 현재 작성한 코드와 장치의 연결 구조

```mermaid
flowchart LR
    ENV[".env / ONTONG_API_KEY"] --> CLIENT["clients/ontong_api.py"]
    REQ["requirements.txt / LangChain, Chroma, HF, httpx"] --> RAG["core/rag.py"]

    CLIENT --> OFFICIAL["공식 API 1순위 / go/ythip/getPlcy / apiKeyNm 사용"]
    CLIENT --> LEGACY["구버전 API 2순위 / opi/youthPlcyList.do"]
    CLIENT --> FALLBACK["웹 검색 JSON 3순위 / pubot/search/portalPolicySearch"]

    OFFICIAL --> NORM["normalize_policy"]
    LEGACY --> NORM
    FALLBACK --> NORM

    COLLECT["scripts/collect_policies.py"] --> CLIENT
    COLLECT --> JSONS["data/policies/*.json / 정책 161개"]

    JSONS --> INDEX["scripts/index_policies.py"]
    INDEX --> DOCS["LangChain Document / 1000자 chunk + 100 overlap"]
    DOCS --> RAG
    RAG --> EMB["BAAI/bge-m3 / HuggingFaceEmbeddings"]
    RAG --> CHROMA["chroma_data / policies collection"]

    SERVICE["services/policy_service.py / policy_search"] --> CLIENT
    SERVICE --> RAG
    SERVICE --> MATCH["나이/지역 매칭 룰"]

    CLIENT --> CAND["candidates"]
    CHROMA --> SEARCH["search policies"]
    SEARCH --> CHUNKS["chunks"]
    MATCH --> MATCHED["matched"]

    CAND --> RESULT["반환 dict"]
    CHUNKS --> RESULT
    MATCHED --> RESULT

    TEST["tests/test_policy_matching.py"] --> MATCH
    NB1["notebooks/01_explore_ontong_api.ipynb"] --> CLIENT
    NB2["notebooks/02_search_quality.ipynb"] --> RAG
```

## 3. `policy_search()` 실행 시 실제 데이터 흐름

```mermaid
sequenceDiagram
    participant User as 호출자
    participant Service as services/policy_service.py
    participant API as clients/ontong_api.py
    participant Ontong as 온통청년 공식 API
    participant RAG as core/rag.py
    participant Chroma as chroma_data policies
    participant Rule as 나이/지역 매칭 룰

    User->>Service: policy_search(profile, query)
    Service->>API: fetch_policies(query, display=10)
    API->>Ontong: GET /go/ythip/getPlcy<br/>apiKeyNm, pageNum, pageSize, rtnType, plcyNm
    Ontong-->>API: youthPolicyList JSON
    API-->>Service: normalized candidates

    Service->>RAG: search("policies", query, k=5)
    RAG->>Chroma: bge-m3 similarity search
    Chroma-->>RAG: top-k policy chunks
    RAG-->>Service: chunks

    Service->>Rule: profile vs candidates
    Rule-->>Service: matched policy ids

    Service-->>User: {"candidates": ..., "chunks": ..., "matched": ...}
```

## 4. 완료/부분완료/미완료 요약

| 영역 | 상태 | 설명 |
|---|---|---|
| 공식 API 호출 | 완료 | `go/ythip/getPlcy` + `apiKeyNm` 성공 확인 |
| 정책 데이터 수집 | 완료 | `data/policies/*.json` 161개 |
| 벡터 DB | 완료 | `chroma_data/`에 `policies` 컬렉션 인덱싱 완료 |
| RAG 검색 | 완료 | `core.rag.search()`로 상위 정책 청크 검색 |
| 단순 정책 검색 함수 | 완료 | `policy_search()`가 `candidates/chunks/matched` 반환 |
| 자격 매칭 | 부분완료 | 나이/지역 구현, 소득분위 매칭은 W12에서 정교화 필요 |
| 표준 Policy Agent | 미완료 | `BaseAgent`, `AgentResponse` 합의 후 W12에 구현 예정 |
| Router/통합 응답 | 미완료 | D 담당 영역 |

## 5. API와 RAG 결합 후보

```mermaid
flowchart TD
    Q["query + profile"] --> API["공식 API 검색"]
    Q --> RAGSEARCH["Chroma RAG 검색"]

    API --> APIIDS["API 후보 policy_id"]
    RAGSEARCH --> RAGIDS["RAG 후보 policy_id"]

    APIIDS --> MERGE["policy_id 기준 병합"]
    RAGIDS --> MERGE

    MERGE --> DETAIL["API plcyNo 단건 조회로 최신 상세 확인"]
    DETAIL --> SCORE["나이, 지역, 소득 룰 점수화"]
    SCORE --> ITEMS["W12 AgentResponse.items"]

    classDef done fill:#d9fbe3,stroke:#16803c,color:#0b3d1c;
    classDef next fill:#fff4cc,stroke:#a66b00,color:#4d3200;

    class API,RAGSEARCH,APIIDS,RAGIDS done;
    class MERGE,DETAIL,SCORE,ITEMS next;
```

검증 결과:

- 공식 API `go/ythip/getPlcy`는 키 기반 호출 성공.
- 공식 API는 `plcyNo` 단건 조회가 가능.
- Chroma는 `policy_id` metadata filter가 가능.
- API 정책명 검색은 표현에 민감하므로 RAG 후보를 살리는 hybrid 방식이 필요.
