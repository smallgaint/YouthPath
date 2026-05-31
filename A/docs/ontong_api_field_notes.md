# 온통청년 API 필드 정리 초안

공식 안내 페이지의 본문에는 구버전 예시가 남아 있다.

```text
https://www.youthcenter.go.kr/opi/youthPlcyList.do
openApiVlak=<인증키>
pageIndex=1
display=10
query=청년취업
bizTycdSel=023010,023020
srchPolyBizSecd=003002001,003002002
keyword=채용,구직,기관
```

다만 같은 페이지의 `JSON 결과 보기` 스크립트는 최신 정책 API를 다음 형태로 안내한다.

```text
https://www.youthcenter.go.kr/go/ythip/getPlcy
apiKeyNm=<인증키>
pageNum=1
pageSize=10
rtnType=json
plcyNm=청년 주거
```

`clients/ontong_api.py`는 최신 `getPlcy`를 먼저 호출하고, 구버전 `youthPlcyList.do`와 웹 통합검색 JSON을 fallback으로 사용한다. 응답 필드명이 조금 달라도 동작하도록 후보 필드명을 넓게 잡았다.

| 내부 필드 | 우선 매핑 후보 |
|---|---|
| `policy_id` | `plcyNo`, `polyBizSjnm`, `bizId`, `policyId`, `id` |
| `title` | `plcyNm`, `polyBizSjnm`, `policyName`, `title`, `name` |
| `description` | `plcySprtCn`, `polyItcnCn`, `description`, `content` |
| `detail` | `plcyExplnCn`, `sporCn`, `detail`, `cnsgNmor` |
| `region` | `zipCd`, `region`, `lclsfNm`, `polyRlmCd`, `area` |
| `category` | `mclsfNm`, `lclsfNm`, `bizTycdSel`, `srchPolyBizSecd`, `category` |
| `min_age` | `sprtTrgtMinAge`, `ageInfo`, `minAge` |
| `max_age` | `sprtTrgtMaxAge`, `ageInfo`, `maxAge` |
| `income` | `earnCndCn`, `income`, `incomeInfo` |
| `deadline` | `aplyYmd`, `rqutPrdCn`, `deadline`, `applyPeriod` |
| `link` | `aplyUrlAddr`, `rfcSiteUrla1`, `link`, `url` |

API가 연결되면 `notebooks/01_explore_ontong_api.ipynb`에서 실제 키 목록을 확인하고 이 표를 갱신한다.
