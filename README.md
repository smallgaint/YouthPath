# YouthPath

Hanyang_Datascience_DeepLearningMethodsandApplications_Project_YouthPath

YouthPath is a multi-agent assistant for youth transition support. A single user query is routed to policy, job, resume, and calendar agents, then merged into one API response for the Streamlit/FastAPI app.

## Current Status

- Router package is connected to Jaewon's FastAPI `/ask` endpoint.
- Policy branch is connected to `A.services.policy_service` with API/RAG/local JSON fallback.
- Job branch attempts Worknet live API first and falls back to deterministic sample data.
- Resume branch attempts Jeonghyun's DART/Naver pipeline first and falls back to rule-based resume context.
- Calendar branch merges policy/job deadlines.
- LUXIA is not live yet, but `LuxiaProvider` is ready. Fill `.env` later to switch from mock to real LUXIA without changing code.

## Project Layout

```text
Router/                         # Router orchestration and LUXIA provider adapter
A/                              # Policy agent: Ontong Youth API, RAG, local policy data
YouthPath-Huiseung/             # Job agent source materials and Worknet implementation
YouthPath-Jeonghyun/            # Resume agent source materials and DART/Naver implementation
YouthPath-jaewon/               # FastAPI backend and Streamlit frontend
docs/YouthPath_architecture.md  # Integrated architecture and current progress
worklog.md                      # Handoff log for continuation
tmp_verify_e2e.py               # File-based E2E verification script
```

## Environment

Use the project virtual environment when running the integrated app:

```powershell
.\.venv\Scripts\python.exe --version
```

The project reads `.env` from the repository root. For local mock runs, only policy-related keys are needed. LUXIA settings can stay commented until the API is issued.

```env
ONTONG_API_KEY=...

# Enable later, after LUXIA API is issued.
# YOUTHPATH_LLM_PROVIDER=luxia
# LUXIA_API_URL=https://.../v1/chat/completions
# LUXIA_API_KEY=...
# LUXIA_MODEL=luxia
# LUXIA_REQUEST_FORMAT=openai
# LUXIA_FALLBACK_TO_MOCK=true
```

## Verify E2E

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe tmp_verify_e2e.py
```

Expected scenarios:

- `job+resume`: verifies Router to FastAPI path with job/resume branches.
- `policy+job+resume+calendar`: verifies policy branch and deadline merge.

Current known fallback:

- If `OpenDartReader` is not installed, Resume live DART/Naver execution falls back to local rule-based context and records the reason in `metadata.agent_errors`.

## Run Router Only

```powershell
.\.venv\Scripts\python.exe -m Router.main
```

This prints the integrated Router JSON response for a sample request.

## Run FastAPI Backend

Because `YouthPath-jaewon` contains a hyphen, run `uvicorn` from inside the backend folder:

```powershell
cd YouthPath-jaewon\YouthPath-jaewon
..\..\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Run Streamlit Frontend

Start the FastAPI backend first. Then open a new terminal at the repository root:

```powershell
.\.venv\Scripts\streamlit.exe run YouthPath-jaewon\YouthPath-jaewon\app.py
```

The Streamlit app sends `POST /ask` requests to:

```text
http://127.0.0.1:8000/ask
```

## LUXIA Switch

Router calls the LLM provider twice:

1. Classification: choose `policy`, `job`, `resume`, and/or `calendar`.
2. Final answer: merge agent outputs into the natural-language `answer`.

For now, `MockLuxiaProvider` fills both roles. When LUXIA is issued, set:

```env
YOUTHPATH_LLM_PROVIDER=luxia
LUXIA_API_URL=...
LUXIA_API_KEY=...
```

Then restart FastAPI. The response schema stays the same:

```json
{
  "answer": "LUXIA natural-language answer",
  "policy": [],
  "job": [],
  "resume": [],
  "calendar": [],
  "metadata": {},
  "error": null
}
```

The structured arrays are intentionally kept for frontend card rendering.
