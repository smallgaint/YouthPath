# 환경 설정

import os
import json
import time
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import requests


# 1. (선택) Google Drive 마운트 - 캐시 영구 저장용
try:
    from google.colab import drive
    drive.mount('/content/drive')
    CACHE_DIR = "/content/drive/MyDrive/youthpath_cache"
except (ImportError, ModuleNotFoundError):
    CACHE_DIR = "./cache"

os.makedirs(CACHE_DIR, exist_ok=True)

# 2. 워크넷 OpenAPI 인증키 (각 API별, 2026-05-10 발급)
WORKNET_KEYS = {
    "채용정보": "060d63ed-85c9-4184-bde0-24d4125579ec",
    "강소기업": "5cf54e8f-c200-47b8-baf1-cf5a26b80119",
    "직무정보": "3de286d2-e3ac-4116-ba47-3d99013f9cde",
    "공통코드": "88af74aa-4b74-4eb8-964d-61a8c1194b02",
    "직업정보": "62d1a8f5-201f-4210-9839-48c9226d2fdc",
}

# 3. 워크넷 OpenAPI 베이스 URL
#    (work24.go.kr 신규 OpenAPI — 발급된 키 형식이 UUID인 경우 이쪽)
WORKNET_BASE = "https://www.work24.go.kr/cm/openApi/call"

# 4. 엔드포인트 경로 (워크넷 문서 확인 후 정확한 값으로 교체)
WORKNET_PATHS = {
    "채용정보": "/wk/callOpenApiSvcInfo210L01.do",  # ⚠️ 실제 경로 확인 필요
    "강소기업": "/wk/callOpenApiSmeList.do",         # ⚠️ 실제 경로 확인 필요
    "직무정보": "/wk/callOpenApiJobInfo.do",         # ⚠️ 실제 경로 확인 필요
    "공통코드": "/wk/callOpenApiCommonCode.do",      # ⚠️ 실제 경로 확인 필요
    "직업정보": "/wk/callOpenApiOccupation.do",      # ⚠️ 실제 경로 확인 필요
}


# worknet_fetcher.py
#
# 워크넷 5종 OpenAPI 통합 클라이언트
#  - 채용정보: 매 질의마다 호출 (메인)
#  - 공통코드 / 직업정보 / 강소기업: 앱 시작 시 1회 로드 → 메모리 캐싱
#  - 직무정보: 24h TTL 캐싱

class WorknetFetcher:
    def __init__(self, keys: dict, base_url: str, paths: dict, cache_dir: str = "./cache"):
        self.keys = keys
        self.base_url = base_url
        self.paths = paths
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # 메모리 캐시 (마스터 데이터 — 거의 안 변함)
        self.region_codes = {}    # 공통코드: "서울" → "11"
        self.career_codes = {}    # 공통코드: "신입" → "1"
        self.edu_codes    = {}    # 공통코드: "대졸" → "03"
        self.job_codes    = {}    # 직업정보: "데이터분석가" → "2236"
        self.strong_sme   = set() # 강소기업: 사업자번호 집합

        # TTL 캐시 (직무정보, 24h)
        self.job_skill_cache = {}  # {job_code: (expires_at, data)}

        # 부팅 시 마스터 데이터 1회 로드
        self._load_master_data()

    # ─── 마스터 데이터 로드 (앱 시작 시 1회) ──────────────────

    def _load_master_data(self):
        print("📦 마스터 데이터 로드 중...")
        self._load_common_codes()
        self._load_occupation_codes()
        self._load_strong_sme()
        print(f"✅ 로드 완료: 지역 {len(self.region_codes)} / "
              f"직무 {len(self.job_codes)} / "
              f"강소기업 {len(self.strong_sme)}")

    def _load_common_codes(self):
        # 공통코드 API → 지역·경력·학력 코드 사전
        # ⚠️ 실제 응답 파싱은 워크넷 문서 확인 후 수정
        try:
            url = self.base_url + self.paths["공통코드"]
            res = requests.get(url, params={
                "authKey": self.keys["공통코드"],
                "returnType": "JSON",
            }, timeout=10)
            res.raise_for_status()
            data = res.json()
            # TODO: 실제 응답 구조에 맞춰 파싱
            # 임시: 하드코딩된 fallback
            raise NotImplementedError("실제 응답 구조 확인 후 파싱")
        except Exception as e:
            # API 응답 구조 확정 전까지 임시 하드코딩
            print(f"   ↳ 공통코드 fallback (이유: {type(e).__name__})")
            self.region_codes = {
                "서울": "11", "부산": "26", "대구": "27", "인천": "28",
                "광주": "29", "대전": "30", "울산": "31", "세종": "36",
                "경기": "41", "강원": "42", "충북": "43", "충남": "44",
                "전북": "45", "전남": "46", "경북": "47", "경남": "48", "제주": "50",
            }
            self.career_codes = {"신입": "1", "경력": "2", "무관": "3"}
            self.edu_codes = {
                "학력무관": "00", "고졸이하": "01", "전문대졸": "02",
                "대졸": "03", "석사": "04", "박사": "05",
            }

    def _load_occupation_codes(self):
        # 직업정보 API → 한국직업분류(KECO) 코드 사전
        # ⚠️ 실제 응답 파싱은 워크넷 문서 확인 후 수정
        try:
            url = self.base_url + self.paths["직업정보"]
            res = requests.get(url, params={
                "authKey": self.keys["직업정보"],
                "returnType": "JSON",
            }, timeout=10)
            res.raise_for_status()
            data = res.json()
            raise NotImplementedError("실제 응답 구조 확인 후 파싱")
        except Exception as e:
            print(f"   ↳ 직업정보 fallback (이유: {type(e).__name__})")
            self.job_codes = {
                "데이터 분석": "2236", "데이터 분석가": "2236", "데이터분석가": "2236",
                "백엔드 개발": "2231", "백엔드 개발자": "2231",
                "프론트엔드 개발": "2232", "프론트엔드 개발자": "2232",
                "AI 엔지니어": "2235", "머신러닝 엔지니어": "2235",
                "기획자": "1320", "서비스 기획자": "1320",
            }

    def _load_strong_sme(self):
        # 강소기업 API → 정부 인증 강소기업 사업자번호 set
        # ⚠️ 실제 응답 파싱은 워크넷 문서 확인 후 수정
        try:
            url = self.base_url + self.paths["강소기업"]
            res = requests.get(url, params={
                "authKey": self.keys["강소기업"],
                "returnType": "JSON",
            }, timeout=10)
            res.raise_for_status()
            data = res.json()
            raise NotImplementedError("실제 응답 구조 확인 후 파싱")
        except Exception as e:
            print(f"   ↳ 강소기업 fallback (이유: {type(e).__name__})")
            self.strong_sme = {"123-45-67890", "234-56-78901"}

    # ─── 룩업 메서드 (메모리 룩업, 외부 호출 0번) ──────────────

    def lookup_region(self, region_name: str):
        return self.region_codes.get(region_name)

    def lookup_job(self, role_name: str):
        if role_name in self.job_codes:
            return self.job_codes[role_name]
        # fuzzy: 부분 일치 fallback
        for k, v in self.job_codes.items():
            if role_name in k or k in role_name:
                return v
        return None

    def lookup_career(self, experience_y: int):
        return self.career_codes["신입"] if experience_y == 0 else self.career_codes["경력"]

    def lookup_edu(self, edu_name: str):
        return self.edu_codes.get(edu_name, self.edu_codes.get("학력무관", "00"))

    def is_strong_sme(self, bizno: str):
        return bizno in self.strong_sme

    # ─── 동적 호출 (매 질의마다) ──────────────────────────────

    def search_jobs(self, filters: dict, display: int = 20):
        """채용정보 API 호출 — 메인 검색"""
        params = {
            "authKey": self.keys["채용정보"],
            "returnType": "JSON",
            "startPage": 1,
            "display": display,
            **filters,
        }
        url = self.base_url + self.paths["채용정보"]
        try:
            res = requests.get(url, params=params, timeout=5)
            res.raise_for_status()
            data = res.json()
            # ⚠️ 실제 응답 구조 확인 후 파싱 경로 수정
            return data.get("wantedRoot", {}).get("wanted", [])
        except Exception as e:
            print(f"⚠️ 채용정보 호출 실패: {e}")
            return []

    def get_job_skills(self, job_code: str) -> dict:
        """직무정보 API — 직무별 필수/우대 스킬 (24h TTL 캐싱)"""
        now = time.time()
        if job_code in self.job_skill_cache:
            expires_at, data = self.job_skill_cache[job_code]
            if now < expires_at:
                return data

        try:
            url = self.base_url + self.paths["직무정보"]
            res = requests.get(url, params={
                "authKey": self.keys["직무정보"],
                "jobCd": job_code,
                "returnType": "JSON",
            }, timeout=5)
            res.raise_for_status()
            payload = res.json()
            skills = {
                "required_skills":  payload.get("coreCompetencies", []),
                "preferred_skills": payload.get("prefCompetencies", []),
            }
        except Exception as e:
            print(f"⚠️ 직무정보 호출 실패 ({job_code}): {e}")
            skills = {"required_skills": [], "preferred_skills": []}

        # 24h 캐싱
        self.job_skill_cache[job_code] = (now + 86400, skills)
        return skills


# job_agent.py
#
# Job Agent — 워크넷 5종 API를 엮어 사용자 질의에 채용공고를 추천
# LLM 호출 0회. 모든 판단은 코드(룰·점수·캐시 룩업).

class JobAgent:
    def __init__(self, fetcher):
        self.fetcher = fetcher

    def search(self, query: str, profile: dict) -> dict:
        """STEP 4-B의 전체 흐름 A→F"""
        t_start = time.time()

        # [A] 텍스트 → 코드 변환 (외부 호출 0번)
        filters = self._build_filters(profile)

        # [B] 채용정보 API 1회 호출
        raw_jobs = self.fetcher.search_jobs(filters, display=20)
        if not raw_jobs:
            return self._error_response(t_start, "채용정보 응답 없음 (필터에 맞는 공고 없음 또는 API 오류)")

        # [C] 정규화 + 강소기업 플래그
        normalized = [self._normalize(j) for j in raw_jobs]
        for j in normalized:
            j["is_strong_sme"] = self.fetcher.is_strong_sme(j["company_bizno"])

        # [D] 직무정보 배치 보강 (unique 코드만 호출)
        unique_codes = {j["job_code"] for j in normalized if j["job_code"]}
        skills_map = {code: self.fetcher.get_job_skills(code) for code in unique_codes}
        for j in normalized:
            sk = skills_map.get(j["job_code"], {"required_skills": [], "preferred_skills": []})
            j["required_skills"] = sk["required_skills"]
            j["preferred_skills"] = sk["preferred_skills"]

        # [E] 적합도 점수 계산 (수식)
        for j in normalized:
            j["fit_score"], j["fit_breakdown"] = self._compute_fit_score(profile, j)

        # [F] 정렬 + 상위 5
        normalized.sort(key=lambda j: j["fit_score"], reverse=True)
        top = normalized[:5]

        return {
            "agent_name": "job",
            "items": top,
            "sources": [
                "worknet:채용정보",
                "worknet:직무정보",
                "worknet:강소기업(cached)",
                "worknet:공통코드(cached)",
                "worknet:직업정보(cached)",
            ],
            "metadata": {
                "latency_ms": int((time.time() - t_start) * 1000),
                "api_calls": {"채용정보": 1, "직무정보": len(unique_codes)},
                "partial": False,
            },
            "error": None,
        }

    # ─── 내부 헬퍼 ────────────────────────────────────────────

    def _build_filters(self, profile: dict) -> dict:
        f = {}
        if region := profile.get("region"):
            if code := self.fetcher.lookup_region(region):
                f["regionCd"] = code
        if role := profile.get("target_role"):
            if code := self.fetcher.lookup_job(role):
                f["jobCd"] = code
        if (exp := profile.get("experience_y")) is not None:
            f["empTpCd"] = self.fetcher.lookup_career(exp)
        if edu := profile.get("education"):
            f["eduLvCd"] = self.fetcher.lookup_edu(edu)
        return f

    def _normalize(self, raw: dict) -> dict:
        """워크넷 raw 응답 → UnifiedJob 스키마"""
        deadline = raw.get("closeDt", "")
        return {
            "wantedAuthNo":       raw.get("wantedAuthNo", ""),
            "title":              str(raw.get("title", "")).strip(),
            "company":            str(raw.get("company", "")).strip(),
            "company_bizno":      raw.get("bizNo", ""),
            "is_strong_sme":      False,
            "location":           raw.get("region", ""),
            "region_code":        raw.get("regionCd", ""),
            "job_code":           raw.get("jobsCd", ""),
            "deadline":           deadline,
            "days_remaining":     self._days_until(deadline),
            "posted_at":          raw.get("regDt", ""),
            "career_required":    raw.get("career", ""),
            "education_required": raw.get("minEdubg", ""),
            "salary": {
                "type":  raw.get("salTpNm", ""),
                "value": self._to_int(raw.get("sal", 0)),
                "unit":  "만원",
            },
            "required_skills":  [],
            "preferred_skills": [],
            "fit_score":     0.0,
            "fit_breakdown": {},
            "source": "worknet",
            "url": f"https://www.work.go.kr/empSpt/empSrch/empSrchView.do?wantedAuthNo={raw.get('wantedAuthNo', '')}",
        }

    def _compute_fit_score(self, profile: dict, job: dict):
        breakdown = {}
        s = 0.0

        # 스킬 매칭 (max 0.4)
        user_skills = {x.lower() for x in profile.get("skills", [])}
        required   = {x.lower() for x in job["required_skills"]}
        if required:
            matched = user_skills & required
            skill_score = 0.4 * (len(matched) / len(required))
        else:
            skill_score = 0.0
        breakdown["skill"] = round(skill_score, 3)
        s += skill_score

        # 경력 매칭 (max 0.3)
        career_score = 0.3 if self._career_matches(
            profile.get("experience_y", 0), job["career_required"]
        ) else 0.0
        breakdown["career"] = career_score
        s += career_score

        # 지역 매칭 (max 0.2)
        region_score = 0.0
        if profile.get("region") and job["location"]:
            if profile["region"] in job["location"]:
                region_score = 0.2
            elif profile["region"].split()[0] in job["location"]:
                region_score = 0.1
        breakdown["region"] = region_score
        s += region_score

        # 마감 긴급도 (max 0.1)
        days = max(job["days_remaining"], 1)
        urgency = round(0.1 * (1.0 / days), 3)
        breakdown["urgency"] = urgency
        s += urgency

        # 강소기업 가산점 (max 0.05)
        if job["is_strong_sme"]:
            breakdown["sme_bonus"] = 0.05
            s += 0.05

        return min(round(s, 3), 1.0), breakdown

    @staticmethod
    def _days_until(date_str):
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
            return (target - date.today()).days
        except Exception:
            return 999

    @staticmethod
    def _career_matches(exp_y, career_required):
        if not career_required:
            return True
        if "신입" in career_required and exp_y == 0:
            return True
        if "경력" in career_required and exp_y > 0:
            return True
        if "무관" in career_required:
            return True
        return False

    @staticmethod
    def _to_int(v):
        try:
            return int(str(v).replace(",", ""))
        except Exception:
            return 0

    def _error_response(self, t_start, message):
        return {
            "agent_name": "job",
            "items": [],
            "sources": [],
            "metadata": {
                "latency_ms": int((time.time() - t_start) * 1000),
                "partial": False,
            },
            "error": {
                "code":    "WORKNET_EMPLOY_UNAVAILABLE",
                "message": message,
            },
        }


# 빠른 작동 확인 — 채용정보 API 모킹 버전
#
# 실제 API 응답 형식 확정 전, 가짜 데이터로 파이프라인이 도는지만 검증

MOCK_WORKNET_RESPONSE = [
    {
        "wantedAuthNo": "K162345789",
        "title":        "데이터분석 신입 채용",
        "company":      "○○데이터",
        "bizNo":        "123-45-67890",
        "region":       "서울 강남구",
        "regionCd":     "11",
        "jobsCd":       "2236",
        "career":       "신입",
        "minEdubg":     "대졸",
        "salTpNm":      "연봉",
        "sal":          "3500",
        "regDt":        "2026-05-08",
        "closeDt":      "2026-05-20",
    },
    {
        "wantedAuthNo": "K162345790",
        "title":        "주니어 데이터 분석가",
        "company":      "△△테크",
        "bizNo":        "234-56-78901",
        "region":       "서울 판교",
        "regionCd":     "11",
        "jobsCd":       "2236",
        "career":       "신입",
        "minEdubg":     "대졸",
        "salTpNm":      "연봉",
        "sal":          "3800",
        "regDt":        "2026-05-09",
        "closeDt":      "2026-05-25",
    },
]

MOCK_JOB_SKILLS = {
    "2236": {
        "required_skills":  ["Python", "SQL", "통계 기초"],
        "preferred_skills": ["Tableau", "추천 시스템"],
    }
}

fetcher = WorknetFetcher(WORKNET_KEYS, WORKNET_BASE, WORKNET_PATHS)

# 채용정보 / 직무정보 호출만 모킹 (다른 마스터 데이터는 fallback 그대로 사용)
fetcher.search_jobs   = lambda filters, display=20: MOCK_WORKNET_RESPONSE
fetcher.get_job_skills = lambda code: MOCK_JOB_SKILLS.get(code, {"required_skills":[], "preferred_skills":[]})

agent = JobAgent(fetcher)

profile = {
    "region":       "서울",
    "target_role":  "데이터 분석가",
    "skills":       ["Python", "SQL"],
    "experience_y": 0,
    "education":    "대졸",
}

result = agent.search(query="데이터 분석가 신입 공고", profile=profile)

print(json.dumps(result, ensure_ascii=False, indent=2))


# 실전 호출 — 실제 워크넷 API로 동작 확인
#
# ⚠️ 실행 전 체크리스트:
#   1. WORKNET_PATHS의 경로들이 실제 워크넷 OpenAPI 문서와 일치하는가
#   2. WorknetFetcher._load_*() 의 응답 파싱 로직이 실제 응답 구조에 맞춰져 있는가
#   3. search_jobs() 의 응답 path("wantedRoot.wanted")가 실제 구조와 일치하는가

# fetcher = WorknetFetcher(WORKNET_KEYS, WORKNET_BASE, WORKNET_PATHS)
# agent = JobAgent(fetcher)
#
# profile = {
#     "region":       "서울",
#     "target_role":  "데이터 분석가",
#     "skills":       ["Python", "SQL"],
#     "experience_y": 0,
#     "education":    "대졸",
# }
#
# result = agent.search(query="데이터 분석가 신입 공고", profile=profile)
#
# import json
# print(json.dumps(result, ensure_ascii=False, indent=2))


# 부분 실패 시나리오 테스트
#
# 직무정보 API만 다운된 경우 → required_skills가 빈 배열이지만
# 채용정보 응답은 정상이라 결과를 보여주되 metadata.partial=True를 명시

fetcher2 = WorknetFetcher(WORKNET_KEYS, WORKNET_BASE, WORKNET_PATHS)
fetcher2.search_jobs   = lambda filters, display=20: MOCK_WORKNET_RESPONSE
fetcher2.get_job_skills = lambda code: {"required_skills": [], "preferred_skills": []}  # 직무정보 다운

agent2 = JobAgent(fetcher2)
result2 = agent2.search(query="데이터 분석가 신입 공고", profile=profile)

print("items 수:", len(result2["items"]))
print("첫번째 fit_score:", result2["items"][0]["fit_score"])
print("required_skills 비었나?:", result2["items"][0]["required_skills"] == [])


# # FastAPI 엔드포인트 예시
#
# from fastapi import FastAPI
# from pydantic import BaseModel
#
# app = FastAPI()
#
# # 앱 시작 시 한 번만 초기화 — 마스터 데이터를 메모리에 적재
# fetcher = WorknetFetcher(WORKNET_KEYS, WORKNET_BASE, WORKNET_PATHS)
# job_agent = JobAgent(fetcher)
#
# class JobRequest(BaseModel):
#     query: str
#     profile: dict
#
# @app.post("/job/search")
# def search_jobs(request: JobRequest):
#     return job_agent.search(
#         query=request.query,
#         profile=request.profile,
#     )
#
# # 실행: uvicorn main:app --reload


# # Streamlit 데모 예시
#
# import streamlit as st
#
# fetcher = WorknetFetcher(WORKNET_KEYS, WORKNET_BASE, WORKNET_PATHS)
# agent = JobAgent(fetcher)
#
# st.sidebar.header("프로필")
# region = st.sidebar.selectbox("거주지", ["서울", "경기", "부산", "대구"])
# target_role = st.sidebar.text_input("희망 직무", "데이터 분석가")
# skills = st.sidebar.multiselect("보유 기술", ["Python", "SQL", "Java", "R"], default=["Python", "SQL"])
# exp = st.sidebar.number_input("경력 (년)", 0, 30, 0)
#
# query = st.text_input("질문", "데이터 분석가 신입 공고 알려줘")
#
# if st.button("🔍 검색"):
#     result = agent.search(query=query, profile={
#         "region": region, "target_role": target_role,
#         "skills": skills, "experience_y": exp, "education": "대졸",
#     })
#     for item in result["items"]:
#         with st.container(border=True):
#             st.subheader(f"{item['company']} — {item['title']}")
#             c1, c2, c3 = st.columns(3)
#             c1.metric("적합도", f"{int(item['fit_score']*100)}%")
#             c2.metric("위치", item['location'])
#             c3.metric("마감", f"D-{item['days_remaining']}")
#             if item["is_strong_sme"]:
#                 st.success("✨ 정부 인증 강소기업")
#             st.caption(f"필수: {', '.join(item['required_skills']) or '-'}")
#             st.caption(f"우대: {', '.join(item['preferred_skills']) or '-'}")
#             st.link_button("해당 사이트로 가기 →", item["url"])
