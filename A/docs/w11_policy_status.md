# W11 팀원 A 진행 현황

## 완료

- Python 3.11.9 가상환경 구성 완료
- `requirements.txt` 설치 완료
- 온통청년 API 키 `.env` 저장 완료
- 온통청년 공식 정책 API `go/ythip/getPlcy` 키 기반 호출 성공
- 구버전 문서 예시 `opi/youthPlcyList.do`가 실패할 때 웹 통합검색 JSON 경로로 fallback 구현
- 정책 JSON 161개 수집 완료
- 공식 API 샘플 응답 5개 저장: `data/api_samples/ontong_official_getPlcy_sample_5.json`
- `core/rag.py` 공통 RAG 헬퍼 구현
- `policies` Chroma 컬렉션 인덱싱 완료
- `policy_search(profile, query)` end-to-end 동작 확인
- 룰 테스트 통과: `4 passed`

## 데이터 분포

```text
주거: 42
금융・복지・문화: 40
일자리: 36
교육・직업훈련: 26
참여・기반: 15
교육: 2
```

## 검색 품질 확인

### 서울 청년 주거 지원

상위 결과가 모두 주거/월세/주거급여 정책으로 나와 의도와 잘 맞는다.

### 30살 이하 창업 지원금

상위 3개가 창업 지원 정책으로 나와 의도와 잘 맞는다.

### 대학생 학자금 대출

교육/학자금 데이터를 추가 수집한 뒤 상위 5개가 모두 학자금 대출이자/교육비 지원으로 개선됐다.

## 데모 명령

```powershell
$env:PYTHONUTF8='1'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
python -c "from services.policy_service import policy_search; print(policy_search({'age':24,'region':'서울'}, '서울 청년 주거 지원').keys())"
```

## 공식 API 확인

- 문서 페이지의 스크립트 기준 최신 정책 API는 `https://www.youthcenter.go.kr/go/ythip/getPlcy`이다.
- 요청 파라미터는 `apiKeyNm`, `pageNum`, `pageSize`, `rtnType=json`이다.
- 정책명 검색에는 `plcyNm` 파라미터가 동작한다.
- 구버전 예시인 `https://www.youthcenter.go.kr/opi/youthPlcyList.do`는 현재 302/timeout이 발생했다.
- 따라서 구현은 `getPlcy`를 1순위, `youthPlcyList.do`를 2순위, 웹 통합검색 JSON을 3순위 fallback으로 둔다.

## 주의

- `bge-m3` 모델은 이미 로컬 HuggingFace cache에 내려받았다. 검색 시 오프라인 모드 환경변수를 켜면 불필요한 HEAD 요청 실패를 피할 수 있다.
