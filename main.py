from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(title="YouthPath API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    user_id: str = "demo_001"
    query: str
    profile: dict[str, Any] = Field(default_factory=dict)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "YouthPath API running"}


@app.post("/ask")
async def ask(req: AskRequest) -> dict[str, Any]:
    """Return a schema-shaped mock response until real agents are connected."""
    profile = _normalize_profile(req.profile)

    policy_result = _mock_policy_agent(req.query, profile)
    job_result = _mock_job_agent(req.query, profile)
    resume_result = _mock_resume_agent(req.query, profile)
    calendar_result = _mock_calendar_agent(policy_result, job_result)

    called_agents = ["policy", "job", "resume", "calendar"]

    return {
        "answer": _mock_integrated_answer(profile),
        "called_agents": called_agents,
        "router": {
            "agents": called_agents,
            "reasoning": "더미 Router: 정책, 채용, 자소서, 일정 예시를 모두 반환합니다.",
            "llm_used": False,
        },
        "policy": policy_result,
        "job": job_result,
        "resume": resume_result,
        "calendar": calendar_result,
    }


def _normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "age": profile.get("age", 27),
        "region": profile.get("region", "서울"),
        "income": profile.get("income") or profile.get("income_bracket") or "중위 60% 이하",
        "education": profile.get("education", "4년제 졸업"),
        "skills": profile.get("skills") or ["Python", "SQL"],
        "experience": profile.get("experience", profile.get("experience_y", 0)),
        "target_role": profile.get("target_role", "데이터 분석가"),
        "target_company": profile.get("target_company", "네이버"),
    }


def _mock_policy_agent(query: str, profile: dict[str, Any]) -> dict[str, Any]:
    items = [
        {
            "policy_id": "POLICY-SEOUL-HOUSING-001",
            "title": "청년월세지원",
            "summary": "서울 거주 청년의 월세 부담을 줄이기 위한 주거비 지원 정책입니다.",
            "benefit": "월 최대 20만원, 최대 12개월 지원",
            "region_label": "서울",
            "category": "주거",
            "keywords": ["월세", "주거지원", "청년"],
            "host_org": "서울특별시",
            "deadline": "2026-05-31",
            "deadline_type": "마감일",
            "deadline_raw": "2026-05-31",
            "score": 1.0,
            "matched_criteria": [
                {
                    "label": "나이",
                    "required": "19~34세",
                    "user_value": f"{profile['age']}세",
                    "ok": True,
                },
                {
                    "label": "지역",
                    "required": "서울",
                    "user_value": str(profile["region"]),
                    "ok": True,
                },
                {
                    "label": "소득",
                    "required": "중위소득 60% 이하",
                    "user_value": str(profile["income"]),
                    "ok": True,
                },
            ],
            "unmatched_criteria": [],
            "other_conditions": [
                {"label": "주택소유", "required": "무주택 청년"},
            ],
            "apply_method": "서울청년포털에서 온라인 신청",
            "exclusion": "주택 소유자 또는 유사 주거지원 중복 수혜자는 제외될 수 있습니다.",
            "link": "https://youth.seoul.go.kr",
            "source": "api+rag",
        },
        {
            "policy_id": "POLICY-HOUSING-LOAN-002",
            "title": "주거안정월세대출",
            "summary": "청년층의 월세 자금 마련을 돕는 저금리 대출 제도입니다.",
            "benefit": "월세 자금 저금리 대출 지원",
            "region_label": "전국",
            "category": "주거",
            "keywords": ["월세대출", "주거안정", "청년"],
            "host_org": "국토교통부",
            "deadline": "2026-06-30",
            "deadline_type": "마감일",
            "deadline_raw": "2026-06-30",
            "score": 0.85,
            "matched_criteria": [
                {
                    "label": "나이",
                    "required": "청년층",
                    "user_value": f"{profile['age']}세",
                    "ok": True,
                },
                {
                    "label": "지역",
                    "required": "전국",
                    "user_value": str(profile["region"]),
                    "ok": True,
                },
            ],
            "unmatched_criteria": [
                {
                    "label": "소득",
                    "required": "세부 소득 기준 확인 필요",
                    "user_value": str(profile["income"]),
                    "ok": False,
                },
            ],
            "other_conditions": [
                {"label": "기타", "required": "임대차계약서 등 증빙서류 필요"},
            ],
            "apply_method": "주택도시기금 또는 취급 은행에서 신청",
            "exclusion": None,
            "link": "https://nhuf.molit.go.kr",
            "source": "api",
        },
    ]

    return {
        "agent_name": "policy",
        "items": items,
        "sources": ["온통청년 getPlcy API", "Chroma policies"],
        "metadata": {
            "latency_ms": 120,
            "query": query,
            "candidate_count": 2,
            "matched_count": len(items),
            "api_path": "mock",
            "region_unresolved": 0,
        },
        "error": None,
    }


def _mock_job_agent(query: str, profile: dict[str, Any]) -> dict[str, Any]:
    items = [
        {
            "wantedAuthNo": "K162345789",
            "title": "데이터분석 신입",
            "company": "OO데이터",
            "company_bizno": "123-45-67890",
            "is_strong_sme": True,
            "location": "서울 강남구",
            "region_code": "11",
            "job_code": "2236",
            "deadline": "2026-06-07",
            "days_remaining": _days_until("2026-06-07"),
            "posted_at": "2026-05-20",
            "career_required": "신입",
            "education_required": "대졸 이상",
            "salary": {"type": "연봉", "value": 3500, "unit": "만원"},
            "required_skills": ["Python", "SQL", "통계 기초"],
            "preferred_skills": ["Tableau", "추천 시스템"],
            "fit_score": 0.87,
            "fit_breakdown": {
                "skill": 0.36,
                "career": 0.30,
                "region": 0.20,
                "urgency": 0.01,
                "sme_bonus": 0.05,
            },
            "source": "worknet",
            "url": "https://www.work.go.kr/empSpt/empSrch/empSrchView.do?wantedAuthNo=K162345789",
        },
        {
            "wantedAuthNo": "K162345790",
            "title": "주니어 데이터 분석가",
            "company": "△△테크",
            "company_bizno": "234-56-78901",
            "is_strong_sme": False,
            "location": "서울 마포구",
            "region_code": "11",
            "job_code": "2236",
            "deadline": "2026-06-15",
            "days_remaining": _days_until("2026-06-15"),
            "posted_at": "2026-05-22",
            "career_required": "신입",
            "education_required": "학력무관",
            "salary": {"type": "연봉", "value": 3200, "unit": "만원"},
            "required_skills": ["SQL", "Excel"],
            "preferred_skills": ["Python", "BI 도구"],
            "fit_score": 0.78,
            "fit_breakdown": {
                "skill": 0.20,
                "career": 0.30,
                "region": 0.20,
                "urgency": 0.01,
            },
            "source": "worknet",
            "url": "https://www.work.go.kr/empSpt/empSrch/empSrchView.do?wantedAuthNo=K162345790",
        },
    ]

    return {
        "agent_name": "job",
        "items": items,
        "sources": [
            "worknet:채용정보",
            "worknet:직무정보",
            "worknet:강소기업(cached)",
            "worknet:공통코드(cached)",
            "worknet:직업정보(cached)",
        ],
        "metadata": {
            "latency_ms": 180,
            "query": query,
            "api_calls": {"채용정보": 1, "직무정보": 1},
            "cache_hits": {"공통코드": 4, "직업정보": 1, "강소기업": 1},
            "partial": False,
        },
        "error": None,
    }


def _mock_resume_agent(query: str, profile: dict[str, Any]) -> dict[str, Any]:
    company = profile["target_company"]
    item = {
        "company": company,
        "company_identifier": "035420",
        "emphasize_keywords": [
            {"keyword": "생성형 AI", "raw_keyword": "AI 서비스", "score": 0.82},
            {"keyword": "검색 플랫폼", "raw_keyword": "검색", "score": 0.78},
            {"keyword": "클라우드/엔터프라이즈", "raw_keyword": "클라우드", "score": 0.72},
        ],
        "matching_points": [
            {"user_skill": "Python", "company_keyword": "생성형 AI", "fit_score": 0.82},
            {"user_skill": "SQL", "company_keyword": "검색 플랫폼", "fit_score": 0.71},
        ],
        "evidence_gaps": ["대규모 트래픽 경험", "엔터프라이즈 서비스 이해"],
        "story_angles": [
            "기술적 깊이: AI/R&D 기반 문제 해결 경험을 기업의 기술 전략과 연결",
            "사용자 경험 개선: 데이터와 검색 기술로 사용자 문제를 해결한 경험 강조",
        ],
        "dynamic_news": [
            {
                "title": f"{company}, AI 서비스 고도화와 엔터프라이즈 전략 강화",
                "link": "https://news.example.com/naver-ai",
            }
        ],
        "static_disclosure_chunks": [
            "DART 공시 기반 더미 청크: 검색, 커머스, 클라우드, AI를 중심으로 사업을 확장하고 있습니다.",
        ],
        "retrieved_chunk_count": 15,
    }
    context_text = (
        f"{company} 지원 시 생성형 AI, 검색 플랫폼, 클라우드/엔터프라이즈 키워드를 "
        "사용자 경험 개선과 데이터 기반 문제 해결 경험에 연결하는 방향이 좋습니다."
    )

    return {
        "agent_name": "resume",
        "items": [item],
        "context_text": context_text,
        "sources": ["ChromaDB companies", "DART disclosure chunks", "Naver News API"],
        "metadata": {
            "latency_ms": 210,
            "query": query,
            "llm_used": False,
            "target_company": company,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "note": "Final answer generation is delegated to the integrated LLM/router.",
        },
        "error": None,
    }


def _mock_calendar_agent(policy_result: dict[str, Any], job_result: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []

    for policy in policy_result["items"]:
        deadline = policy.get("deadline")
        if deadline:
            items.append(
                {
                    "event_id": f"policy:{policy['policy_id']}",
                    "title": f"{policy['title']} 마감",
                    "deadline": deadline,
                    "days_remaining": _days_until(deadline),
                    "link": policy.get("link"),
                    "source": "policy",
                    "is_pinned": False,
                    "auto_filled": True,
                }
            )

    for job in job_result["items"]:
        deadline = job.get("deadline")
        if deadline:
            items.append(
                {
                    "event_id": f"job:{job['wantedAuthNo']}",
                    "title": f"{job['company']} {job['title']} 마감",
                    "deadline": deadline,
                    "days_remaining": _days_until(deadline),
                    "link": job.get("url"),
                    "source": "job",
                    "is_pinned": False,
                    "auto_filled": True,
                }
            )

    items.sort(key=lambda item: item["days_remaining"])

    return {
        "agent_name": "calendar",
        "items": items,
        "sources": ["policy.deadline", "job.deadline"],
        "metadata": {
            "latency_ms": 20,
            "auto_filled_count": len(items),
            "pinned_only": False,
        },
        "error": None,
    }


def _mock_integrated_answer(profile: dict[str, Any]) -> str:
    return f"""
{profile['region']} 거주 {profile['age']}세 기준으로 정책, 채용, 자소서 준비 포인트, 마감 일정을 함께 정리했어요.

정책은 청년월세지원이 현재 프로필과 가장 잘 맞습니다. 나이, 지역, 소득 조건이 모두 충족되는 예시라 우선 확인할 만합니다. [출처: 온통청년 getPlcy API, Chroma policies]

채용은 OO데이터의 데이터분석 신입 공고가 {', '.join(profile['skills'])} 역량과 잘 맞는 예시입니다. 적합도는 87%로 계산했습니다. [출처: worknet]

{profile['target_company']} 자소서 준비는 생성형 AI, 검색 플랫폼, 클라우드/엔터프라이즈 키워드를 본인의 프로젝트 경험과 연결하는 방향이 좋습니다. [출처: DART disclosure chunks, Naver News API]

다음 단계는 청년월세지원 신청 조건 확인, OO데이터 공고 지원 준비, 마감 일정 캘린더 저장입니다.
""".strip()


def _days_until(date_str: str) -> int:
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return 999
    return (target - date.today()).days
