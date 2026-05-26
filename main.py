from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="YouthPath API")

# Streamlit 연결 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Request Model
# =========================

class AskRequest(BaseModel):
    query: str
    profile: dict


# =========================
# Root
# =========================

@app.get("/")
async def root():
    return {"message": "YouthPath API running"}


# =========================
# Ask Endpoint
# =========================

@app.post("/ask")
async def ask(req: AskRequest):

    # 지금은 더미 데이터
    # 나중에 여기 Router Agent 연결

    return {
        "answer": f"""
서울 거주 기준으로 정책과 채용 정보를 정리했어요.

정책:
청년월세지원이 조건에 가장 적합합니다.
신청 마감은 5월 31일입니다.

채용:
OO회사 데이터분석 신입 채용이 적합합니다.
마감까지 8일 남았습니다.
""",

        "policy": [
            {
                "title": "청년월세지원",
                "deadline": "2026-05-31",
                "description": "만 19~34세 청년 대상 월세 지원",
                "link": "https://example.com/policy1",
                "match": "나이 27세, 서울 거주 조건 충족"
            },
            {
                "title": "주거안정월세대출",
                "deadline": "2026-06-30",
                "description": "청년 대상 저금리 월세 대출",
                "link": "https://example.com/policy2",
                "match": "연소득 기준 충족"
            }
        ],

        "job": [
            {
                "company": "OO회사",
                "title": "데이터분석 신입",
                "deadline": "D-8",
                "date": "2026-05-20",
                "link": "https://example.com/job"
            }
        ],

        "calendar": [
            {
                "title": "OO회사 데이터분석 신입",
                "date": "2026-05-20",
                "type": "채용"
            },
            {
                "title": "청년월세지원 마감",
                "date": "2026-05-31",
                "type": "정책"
            }
        ]
    }
