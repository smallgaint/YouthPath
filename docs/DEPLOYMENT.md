# YouthPath 배포 가이드 (클라우드 VM — AWS EC2 / GCP)

이 문서는 **클라우드 VM(Ubuntu) 한 대에 YouthPath를 배포**하는 방법을 처음 하는 사람도 따라 할 수 있게 정리한 것입니다.
명령어는 위에서부터 **순서대로 복사-붙여넣기** 하면 됩니다.

---

## 0. 전체 그림 (먼저 이해하기)

YouthPath는 **한 대의 VM 안에서 2개의 프로세스**가 같이 돕니다.

```
[사용자 브라우저]
      │  (80/443 또는 8501 포트)
      ▼
[Streamlit 프론트엔드 :8501] ──HTTP──▶ [FastAPI 백엔드 :8000(내부)]
                                              │
                                              ▼
                              온통청년 / 공공데이터 / DART / NAVER / LUXIA API
```

- 프론트(Streamlit)는 같은 VM의 `127.0.0.1:8000` 으로 백엔드를 호출하므로 **둘 다 같은 VM에서 켜야** 합니다.
- 8000은 **외부에 열 필요 없음**(내부 통신용). 외부에 여는 건 8501(또는 80/443)뿐.
- API 키는 `.env` 파일에 넣고, 이 파일은 **GitHub에 올라가지 않으므로 VM에서 직접 만들어야** 합니다.

### VM 사양 권장
- OS: **Ubuntu 22.04 LTS**
- 사양: **2 vCPU / RAM 8GB / 디스크 30GB 이상**
  (torch·transformers·sentence-transformers 등 무거운 패키지 + 임베딩 모델 때문에 RAM 4GB는 빠듯합니다.)

---

## 0.5 인스턴스 사양 · 비용 · S3/DynamoDB (꼭 읽기)

### ⭐ 핵심: 답변 생성 LLM은 EC2가 아니라 "LUXIA 클라우드"에서 돈다
이 앱은 답변을 만들 때 `bridge.luxiacloud.com` 으로 **API 호출만** 합니다.
즉 **EC2에는 GPU나 대형(m7 등) 인스턴스가 필요 없습니다.** EC2가 쓰는 무거운 자원은
RAG/Resume용 **임베딩 모델(sentence-transformers, CPU)** 의 RAM뿐입니다.

| 무엇이 어디서 도나 | 위치 | EC2 사양 영향 |
|---|---|---|
| **답변 생성(LUXIA LLM)** | **LUXIA 클라우드(외부 API)** | ❌ 없음 (GPU/m7 불필요) |
| 임베딩 모델(RAG/Resume) | EC2 (CPU) | RAM만 필요 |
| FastAPI + Streamlit | EC2 (CPU) | 적당한 RAM |

> ⚠️ "LLM 답변이 잘 생성되는지" 는 **인스턴스 크기와 무관**합니다. 답변이 끊기면 인스턴스를
> 키울 게 아니라 LUXIA 쪽을 봐야 합니다 → `.env`의 `LUXIA_TIMEOUT`(타임아웃)·`max_tokens`(길이),
> 또는 LUXIA 서버 장애(503) 시 자동 Mock 폴백(`LUXIA_FALLBACK_TO_MOCK=true`).
>
> **GPU 인스턴스(g5 등)는 LUXIA 대신 EC2에 직접 LLM(Llama·HyperCLOVA 등)을 띄울 때만** 필요합니다.

### 인스턴스 타입 / RAM 가이드
| 인스턴스 | vCPU/RAM | 데모 가능? |
|---------|----------|-----------|
| t3.micro (**프리티어**) | 2 / **1GB** | ❌ 설치·모델 로딩 중 OOM(메모리부족)으로 죽음 → **프리티어로는 불가** |
| **t3.small** | 2 / **2GB** | ⚠️ 빠듯 — **스왑 4GB 추가하면 데모 가능** (아래 스왑 설정) |
| **t3.medium** | 2 / 4GB | 🙆 권장(안정적) |
| t3.large | 2 / 8GB | 😌 여유 |

### 비용 (프리티어 안 되면 "1달러"는 가능)
- EC2는 **켜져 있는 시간만큼** 과금됩니다 (t3.small ≈ 시간당 약 $0.023).
- **데모 때만 켜고 끝나면 인스턴스 Stop** → 몇 시간이면 **1~2달러 이내**.
- ❗ **Stop = 과금 거의 멈춤**(EBS 디스크 소액만). **Terminate = 인스턴스+데이터 삭제** 이므로 주의.

### t3.small 선택 시 스왑(swap) 4GB 추가 (필수)
RAM 2GB로는 부족하니 스왑을 더해 데모를 버티게 합니다.
```bash
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h   # Swap 4.0Gi 표시 확인
```

### S3 / DynamoDB 가 필요한가?
**기본 데모에는 필요 없습니다.** 이 앱의 데이터는 전부 VM 로컬 파일로 동작합니다.

| 데이터 | 현재 방식 | S3/DynamoDB |
|--------|----------|-------------|
| 회원/프로필/저장일정 | `users.json` (로컬 파일) | ❌ 선택(영속성 강화 시 DynamoDB) |
| 기업 공시 인덱스 | `chroma_db/` (로컬 파일) | ❌ 선택(백업 시 S3) |

- **EC2 한 대만으로 데모는 충분.** (EBS에 저장되므로 Stop 후에도 데이터 유지)
- **단, 수업 과제에서 "S3·DynamoDB 사용"이 요구사항이면** 별도 연동이 필요합니다:
  - 회원 DB: `users.json` → **DynamoDB** 테이블로 이전
  - 정적/백업/공시 인덱스: **S3** 버킷 사용
  - 이 연동 코드가 필요하면 팀에 요청하세요(현재 코드엔 미포함).

---

## 1. VM 만들기 + 포트 열기

### AWS EC2
1. EC2 → 인스턴스 시작 → Ubuntu 22.04, `t3.large`(2vCPU/8GB) 정도 선택
2. **보안 그룹(Security Group) 인바운드 규칙**에 추가:
   - SSH: TCP **22** (내 IP)
   - HTTP: TCP **80** (0.0.0.0/0)  ← nginx 쓸 경우
   - (nginx 없이 바로 띄울 거면) TCP **8501** (0.0.0.0/0)
3. 키페어(.pem) 받아서 SSH 접속:
   ```bash
   ssh -i my-key.pem ubuntu@<VM의_퍼블릭_IP>
   ```

### GCP (Compute Engine)
1. VM 인스턴스 만들기 → Ubuntu 22.04, e2-standard-2(2vCPU/8GB)
2. **방화벽**에서 `tcp:80`, `tcp:8501` 허용 (또는 "HTTP 트래픽 허용" 체크)
3. 브라우저 SSH 또는 `gcloud compute ssh` 로 접속

---

## 2. 기본 패키지 설치 (VM 안에서)

```bash
sudo apt update && sudo apt install -y python3.10 python3.10-venv python3-pip git
```

---

## 3. 코드 받기

```bash
cd ~
git clone -b deploy https://github.com/smallgaint/YouthPath.git
cd YouthPath
```

> `-b youthpath-integration` 은 배포할 브랜치입니다. main에 머지했다면 `-b main` 으로 바꾸세요.

---

## 4. 가상환경 + 의존성 설치

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r A/requirements.txt numpy OpenDartReader \
  beautifulsoup4 lxml scikit-learn keybert fastapi uvicorn streamlit pandas
```

> 무거운 패키지(torch 등) 때문에 5~10분 걸릴 수 있습니다.

---

## 5. 환경변수(.env) 만들기 ⚠️ 가장 중요

```bash
cp .env.sample .env
nano .env      # 또는 vim .env
```

`.env.sample` 의 주석을 보고 발급받은 키를 채웁니다. 최소한 아래는 채워야 실데이터가 나옵니다:
- `ONTONG_API_KEY` (정책)
- `PUBLIC_RECRUIT_SERVICE_KEY` (채용)
- `DART_API_KEY`, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` (자소서)
- `LUXIA_API_KEY` (없으면 자동 Mock 폴백)
- `CHROMA_DB_PATH` 는 **VM의 절대경로**로:
  ```
  CHROMA_DB_PATH=/home/ubuntu/YouthPath/chroma_db
  ```

저장: nano는 `Ctrl+O` → `Enter` → `Ctrl+X`.

---

## 6. (선택) Resume 기업 공시 인덱싱

자소서(Resume) 기능에서 특정 기업을 보려면 먼저 인덱싱해야 합니다.

```bash
.venv/bin/python index_company.py 네이버 035420
.venv/bin/python index_company.py 카카오 035720
```

---

## 7. 먼저 수동 실행으로 동작 확인

터미널 2개(또는 tmux)로:

```bash
# 터미널 1 — 백엔드
cd ~/YouthPath/YouthPath-jaewon/YouthPath-jaewon
../../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 터미널 2 — 프론트 (외부 접속 위해 0.0.0.0)
cd ~/YouthPath/YouthPath-jaewon/YouthPath-jaewon
../../.venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

브라우저에서 `http://<VM_퍼블릭_IP>:8501` 접속해 확인합니다.
잘 되면 `Ctrl+C` 로 끄고, 아래 8번으로 **자동 실행(systemd)** 을 설정합니다.

---

## 8. 자동 실행 설정 (systemd) — 재부팅·종료에도 계속 켜짐

> 경로의 `ubuntu` 와 `/home/ubuntu/multibot` 은 실제 사용자/경로에 맞게 바꾸세요.

### 8-1. 백엔드 서비스

```bash
sudo nano /etc/systemd/system/youthpath-api.service
```

```ini
[Unit]
Description=YouthPath FastAPI backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/YouthPath/YouthPath-jaewon/YouthPath-jaewon
ExecStart=/home/ubuntu/YouthPath/.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 8-2. 프론트엔드 서비스

```bash
sudo nano /etc/systemd/system/youthpath-web.service
```

```ini
[Unit]
Description=YouthPath Streamlit frontend
After=network.target youthpath-api.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/YouthPath/YouthPath-jaewon/YouthPath-jaewon
ExecStart=/home/ubuntu/YouthPath/.venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
```

### 8-3. 등록 + 시작

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now youthpath-api youthpath-web
sudo systemctl status youthpath-api youthpath-web   # 둘 다 active(running) 확인
```

이제 `http://<VM_퍼블릭_IP>:8501` 로 상시 접속됩니다.

---

## 9. (권장) nginx 리버스 프록시 + 도메인/HTTPS

`:8501` 없이 깔끔한 주소(80/443)로 접속하려면 nginx를 둡니다.

```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/youthpath
```

```nginx
server {
    listen 80;
    server_name <도메인_또는_VM_IP>;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # Streamlit은 웹소켓을 쓰므로 아래 두 줄 필수
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/youthpath /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

이제 `http://<도메인_또는_IP>` 로 접속됩니다. (이 경우 보안그룹에서 8501은 닫아도 됩니다.)

### HTTPS (도메인이 있을 때)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d <도메인>
```

---

## 10. 자주 막히는 부분 (체크리스트)

| 증상 | 원인 / 해결 |
|------|------------|
| 브라우저에서 접속 안 됨 | 보안그룹/방화벽에 **8501(또는 80)** 인바운드 열었는지 |
| 화면은 뜨는데 검색하면 에러 | 백엔드(:8000)가 안 켜짐 → `systemctl status youthpath-api` |
| 답변이 `[MOCK_LUXIA]` | LUXIA 키 미설정/장애 → `.env` 의 `LUXIA_*` 확인 (정상 동작이며, 카드 데이터는 실데이터) |
| 정책/채용이 비어 있음 | 해당 API 키 미설정 → 응답 `metadata.agent_errors` 확인, `.env` 키 점검 |
| 자소서에 "인덱싱되지 않은 기업" | 6번 `index_company.py` 로 그 기업을 먼저 인덱싱 |
| 설치 중 메모리 부족/Killed | VM RAM 부족 → 8GB 이상으로 |
| 코드 업데이트 반영 | `git pull` 후 `sudo systemctl restart youthpath-api youthpath-web` |

---

## 11. 보안 주의 (반드시)

- **`.env` 와 `users.json` 은 절대 GitHub에 올리지 않습니다** (이미 `.gitignore` 처리됨). VM에서 직접 만든 `.env` 도 그대로 둡니다.
- API 키가 노출되면 즉시 재발급하세요.
- 가능하면 SSH는 키 인증만 사용하고, 보안그룹에서 22번은 본인 IP로 제한하세요.

---

문의나 막히는 부분이 생기면, 해당 명령어의 **에러 메시지 전체**와 `systemctl status` 결과를 캡처해서 공유하면 빠르게 해결할 수 있습니다.
