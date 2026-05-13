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

---

## 5/13 회의 추가 의제 — E와 합의할 배포 전략

5/12 회의가 5/13으로 연기되면서, EC2 배포 시 `chroma_data/` 운영 방식을 결정해야 한다. 핵심은 **"인덱싱"이라는 작업이 무엇이며, 그 결과물을 어떻게 운반/유지할 것인가**이다.

### "인덱싱"이 무엇인가

`scripts/index_policies.py`가 수행하는 일련의 작업을 인덱싱이라 부른다. 구체적으로 다음 4단계를 거친다.

1. **정책 JSON 로드**: `data/policies/*.json` 161개 파일을 메모리로 불러온다.
2. **텍스트 합성·청킹**: 각 정책의 필드(정책명, 분야, 지역, 나이, 소득, 신청기간, 설명, 상세 등)를 하나의 문서로 합치고, 1000자 + 100자 overlap으로 청크 단위 분할한다.
3. **임베딩 생성**: 각 청크를 `BAAI/bge-m3` 모델로 1024차원 벡터로 변환한다. 이 단계가 가장 무겁다. 모델은 약 2GB이며 첫 실행 시 HuggingFace에서 다운로드된다.
4. **Chroma 저장**: 생성한 벡터와 metadata를 `chroma_data/` 디렉토리에 영구 저장한다. 결과물은 두 가지이다.
   - `chroma.sqlite3`: 메타데이터·문서 본문 저장 SQLite 파일
   - `c68afd32-2f52-4014-b9de-5b4763aafca5/`: 벡터 인덱스 바이너리 파일 디렉토리

이 두 산출물이 합쳐져야 `core.rag.search()`가 동작한다. 즉, **인덱싱은 "검색 가능한 상태의 Vector DB 산출물을 만드는 작업"**이고, 이 산출물(`chroma_data/`)을 어디서·언제 만들지가 배포 전략의 핵심이 된다.

### 방식 A — chroma_data를 Docker 이미지에 포함

```dockerfile
COPY chroma_data/ /app/chroma_data/
```

로컬에서 인덱싱을 1회 수행하고, 그 결과물을 Docker 이미지에 통째로 복사한다. EC2에 이미지를 배포하면 컨테이너가 시작하자마자 검색이 가능하다.

- 장점:
  - 컨테이너 부팅 즉시 서비스 가능
  - 외부 의존성 없음 (API 키, 모델 다운로드 불필요)
  - 동일한 빌드는 동일한 검색 결과를 보장 (재현성)
- 단점:
  - 이미지 크기가 커진다 (벡터·SQLite 모두 포함)
  - 정책이 갱신될 때마다 이미지 재빌드 + 재배포가 필요하다
  - 운영 중 새 정책 반영 불가

### 방식 B — 코드만 이미지에 넣고 EC2에서 재인덱싱

```dockerfile
COPY . /app/
# .dockerignore에 chroma_data/ 추가
```

EC2 컨테이너가 시작한 뒤 내부에서 인덱싱 스크립트를 직접 실행한다.

```powershell
python scripts/collect_policies.py --max-items 200
python scripts/index_policies.py
```

- 장점:
  - 이미지가 가볍다
  - 운영 중 정책 갱신 가능 (cron으로 주 1회 재수집·재인덱싱)
  - 항상 최신 정책 데이터로 서비스 가능
- 단점:
  - 첫 부팅 시간이 길다 (bge-m3 다운로드 + API 호출 + 임베딩 생성 수 분)
  - EC2에 `ONTONG_API_KEY` 환경변수 주입 필요
  - 인덱싱 중에는 서비스 응답 불가 (또는 검색 품질 저하)
  - 컨테이너가 재시작될 때마다 인덱싱이 반복되면 시간/비용 낭비

### 절충안 — 이미지 + 영구 볼륨 + 주기적 재인덱싱

실무에서 가장 흔히 쓰는 방식이며, 본 프로젝트에도 적합하다. 핵심 아이디어는 "이미지에는 코드만, 인덱스 산출물은 별도 저장소에 영구 보관"이다.

```text
1. Docker 이미지에는 코드와 의존성만 포함 (chroma_data 미포함)
2. EC2에 EBS 영구 볼륨을 붙이고, /app/chroma_data로 마운트
3. 컨테이너 첫 부팅 시 인덱싱 1회 수행 → EBS에 저장
4. 컨테이너 재시작 시에는 EBS에 이미 산출물이 있으므로 재인덱싱 없이 즉시 서비스
5. cron 작업으로 주 1회(또는 일 1회) 정책 재수집·재인덱싱 → 새 EBS 산출물로 덮어쓰기
```

추가로 S3를 활용한 백업·복구 전략을 같이 둘 수 있다.

```text
- S3 버킷에 chroma_data의 일일 스냅샷 업로드 (tar.gz)
- 신규 EC2 인스턴스 부팅 시 S3에서 최신 스냅샷을 받아 EBS에 복원
- 인덱싱은 EC2에서 1회만 하고, 다른 인스턴스는 스냅샷으로 빠르게 기동
```

- 장점:
  - 컨테이너 재시작이 빠르다 (이미 EBS에 인덱스가 있으므로)
  - 정책 갱신 가능 (cron 재인덱싱)
  - 인스턴스 확장 시 S3 스냅샷 복원으로 빠른 기동
  - 이미지 크기가 가볍다
- 단점:
  - 구성 요소가 늘어난다 (EC2 + EBS + S3 + cron)
  - EBS 비용이 추가된다 (약 $0.1/GB/월)
  - 인덱스 갱신 시점에 EBS 락(lock) 또는 별도 디렉토리로 swap 전략 필요

### E와 합의해야 할 핵심 질문

- EC2 인스턴스에 EBS 영구 볼륨을 붙일 것인가? 아니면 컨테이너 내부 ephemeral 디스크만 사용할 것인가?
- 정책 데이터 갱신 주기는? (매일/주 1회/수동)
- 첫 컨테이너 부팅에서 bge-m3 다운로드 + 인덱싱(수 분)을 허용 가능한가, 아니면 즉시 서비스가 필요한가?
- 데모 단계와 운영 단계에서 다른 방식을 쓸 수 있는데, 발표 데모는 어느 쪽으로 가는가?

### A 파트 기본 입장

- 데모 단계: 방식 A (chroma_data 이미지 포함)가 단순하고 재현성 좋다.
- 운영 단계: 절충안 (이미지 + EBS + cron 재인덱싱)이 정책 갱신과 운영 부담을 동시에 해결한다.

---

## RAG 텍스트 보강 결과 (5/13 작업)

회의 직전에 RAG 인덱싱 텍스트를 API raw 필드 전체를 활용하도록 확장했다. 결과를 공유하고 W12 이후 추가 보강 여부를 논의한다.

### 결과 요약

| 항목 | Before | After |
|---|---|---|
| 정책당 평균 텍스트 | 약 200자 | 558자 (약 2.5배) |
| 다청크 정책 수 | 0개 | 16개 (1000자 초과로 분할) |
| 최대 정책 텍스트 | 약 300자 | 3,370자 |
| 총 청크 수 | 161 | 177 |
| 자격조건/제출서류 검색 | 불가 | 가능 |

### 새로 들어간 raw 필드

`PLCY_SPRT_CN` 지원내용, `ADD_APLY_QLFC_CND_CN` 자격조건 상세, `PLCY_APLY_MTHD_CN` 신청방법, `SRNG_MTHD_CN` 심사방법, `SBMSN_DCMNT_CN` 제출서류, `PTCP_PRP_TRGT_CN` 지원제외, `ETC_MTTR_CN` 기타사항, `EARN_ETC_CN` 소득조건 상세, `PLCY_KYWD_NM` 키워드, `BIZ_PRD_ETC_CN` 사업기간, `MRG_STTS_NM` 결혼상태, `QLFC_ACBG_NM` 학력조건, `EMPM_STTS_NM` 취업상태, `MJR_CND_NM` 전공조건, `SPCL_FLD_NM` 특별분야.

### 검색 품질 검증

5개 데모 쿼리 모두 의도와 일치하는 결과를 반환했다. 특히 `"청년 월세 자격 조건 소득"` 쿼리에서 옹진군 청년월세 정책의 **자격조건 텍스트 청크가 1위**로 잡혔다. 이전 인덱싱(메타데이터만)에서는 절대 불가능했던 검색이다.

### metadata 스키마 확장

각 청크 metadata에 다음을 추가했다.

```python
"source": "api_raw",       # 출처 표시
"source_priority": 3,      # 1=PDF, 2=HTML, 3=API (낮을수록 디테일)
"source_url": "...",       # REF_URL_ADDR1 또는 link
```

W12 Policy Agent에서 검색 결과 재랭킹할 때 `source_priority`를 가중치로 활용 가능하다.

---

## API보다 더 디테일한 출처 보강 — 검토 결과와 향후 작업

원래 설계 의도는 "API에서 대략 후보를 찾고, RAG에서 더 디테일한 정보를 찾는" 구조였다. 현재 RAG의 원천이 API와 동일하므로, 출처를 PDF/HTML 본문으로 확장하면 두 검색이 서로 다른 가치를 만들 수 있다. 5/13 시도 결과를 정리하고 W12-W13 작업 후보로 남긴다.

### 시도 1 — `REF_URL_ADDR1` HTTP GET + trafilatura 본문 추출

8개 도메인 시범 결과, 실질적으로 사용 불가능했다.

| 도메인 | 결과 |
|---|---|
| youth.chungnam.go.kr (34건) | 개인정보처리방침 boilerplate만 추출 |
| youth.incheon.go.kr (24건) | 자격조건 일부 (479자, 빈약) |
| www.ulsan.go.kr (13건) | 제목만 |
| youth.gwangju.go.kr (9건) | 사이트 메뉴만 |
| www.asan.go.kr (7건) | 정책 키워드 0회 |

원인: 한국 청년정책 포털(youth.X.go.kr)은 모두 SPA로 만들어져 정적 HTML에는 메뉴와 스크립트만 들어있다. 본문은 jQuery/AJAX로 비동기 로드된다.

### 시도 2 — 온통청년 자체 상세 페이지

URL 패턴: `https://www.youthcenter.go.kr/youthPolicy/ythPlcyTotalSearch/ythPlcyDetail/{DOCID}`

페이지 자체는 200 OK를 반환하지만 정적 HTML은 빈 템플릿이다. Googlebot User-Agent로 SSR 우회를 시도해도 동일. 내부 AJAX endpoint는 Vue/React 번들 안에 캡슐화되어 발견 불가.

### 시도 3 — API raw의 `ATCH_FILE_MNG_SN`으로 PDF 직접 다운로드

161개 정책 중 67개(41.6%)가 `ATCH_FILE_MNG_SN`을 보유. 그러나 온통청년의 실제 다운로드 endpoint는 `/framework/filedownload/keisDownload.do?filePathName=<인코딩>&realFlnm=<인코딩>` 형태로 인코딩된 path를 받는다. `ATCH_FILE_MNG_SN`만으로는 다운로드 URL을 만들 수 없다.

### 시도 4 — 지자체 게시판(SAEOL) 정적 페이지

양산시 케이스 검증 결과, **www.X.go.kr 형식의 지자체 시청 게시판(예: 양산시 saeol/gosi/view.do)은 본문이 정적 HTML에 들어있다.** trafilatura가 본문 영역을 인식하지 못한 것이지 데이터는 노출되어 있었다. BeautifulSoup으로 특정 div를 직접 추출하면 가능하다.

```
양산시 게시판 정적 HTML에 노출된 내용:
- "양산시에서 대학생들의 학자금 대출에 따른 이자부담을 덜어주기 위해..."
- □ 지원대상, □ 신청기간, □ 지원내용, □ 신청방법 모두 정적 노출
```

### 결론과 5/13 결정

W11 데모 시점에는 RAG 텍스트 보강을 **Phase 1 (API raw 필드 전체 활용)** 까지만 적용한다. Phase 2/3는 W12-W13에서 다음 두 갈래 중 하나로 진행 후보다.

1. **정적 지자체 게시판 한정 BeautifulSoup 추출** — `www.X.go.kr` 형식만 자동 식별하여 별도 파서 작성. 161건 중 30-50% 정도 추가 보강 가능 추정. 작업량 2-3시간.
2. **Playwright 헤드리스 브라우저로 동적 사이트까지 전체 추출** — Chromium ~200MB 설치 후 161건 × 5-10초 = 20-30분 크롤링. 사이트별 팝업/로딩 패턴 차이로 안정성 우려. 작업량 4-6시간.

Phase 1만으로도 검색 품질이 2.5배 개선되어 W11 데모와 5/13 회의용으로는 충분하다고 판단한다.

### 보존된 산출물

- `scripts/index_policies.py` — raw 필드 전체 활용 인덱싱 (Phase 1 적용 완료)
- `scripts/enrich_policies_html.py` — Phase 2 시범 크롤링 스크립트. 현재 단순 GET으로는 부실한 결과만 나오지만, W13에서 Playwright와 결합하면 재활용 가능
- `chroma_data/` — Phase 1 적용 후 재인덱싱된 상태 (177 청크)
