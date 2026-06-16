import sys
from pathlib import Path
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from Router.router import YouthPathRouter

app = FastAPI(title="YouthPath API")
router = YouthPathRouter()

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
    user_id: str | None = None


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
    try:
        return router.invoke({"query": req.query, "profile": req.profile, "user_id": req.user_id})
    except Exception as e:
        tb_str = traceback.format_exc()
        print("="*60)
        print("🚨 UNHANDLED EXCEPTION IN /ask ENDPOINT")
        print(tb_str)
        print("="*60)
        return JSONResponse(
            status_code=500,
            content={
                "answer": "죄송합니다, 요청을 처리하는 중 서버에서 예상치 못한 오류가 발생했습니다. 서버 로그를 확인해주세요.",
                "policy": [],
                "job": [],
                "resume": [],
                "calendar": [],
                "metadata": {},
                "error": f"Internal Server Error: {e.__class__.__name__}: {e}",
            },
        )
