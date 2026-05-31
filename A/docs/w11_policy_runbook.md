# W11 Policy RAG 실행 순서

## 1. Python 3.11 준비

현재 로컬 셸에서는 `python` 실행이 실패하고 `py` 런처도 설치된 Python을 찾지 못했다. Python 3.11이 잡힌 뒤 아래를 실행한다.

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

## 2. API 1~2개만 테스트

```powershell
python -c "from clients.ontong_api import fetch_policies; r=fetch_policies(query='청년 주거', display=2); print(len(r['items'])); print(r['items'][0].keys() if r['items'] else 'no items')"
```

## 3. 정책 50개 이상 수집

API 응답 구조가 정상으로 확인된 뒤에만 실행한다.

```powershell
python scripts/collect_policies.py --max-items 60 --display 10
```

## 4. Chroma 인덱싱

첫 실행은 `BAAI/bge-m3` 모델 다운로드 때문에 오래 걸릴 수 있다.

```powershell
python scripts/index_policies.py --chunk-size 1000 --overlap 100
```

## 5. 검색 테스트

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
python -c "from core.rag import search; print(search('policies', '서울 청년 주거 지원', k=5))"
```

## 6. 단순 정책 서비스 테스트

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
python -c "from services.policy_service import policy_search; print(policy_search({'age':24,'region':'서울'}, '서울 청년 주거 지원').keys())"
```

## 7. 룰 테스트

```powershell
pytest tests/test_policy_matching.py -v
```
