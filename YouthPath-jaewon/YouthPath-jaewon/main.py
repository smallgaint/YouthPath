import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
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
    return router.invoke({"query": req.query, "profile": req.profile, "user_id": req.user_id})
