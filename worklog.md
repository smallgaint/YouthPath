# WORKLOG

- Last updated: 2026-06-01
- Scope: YouthPath multi-agent integration (A + Huiseung + Jaewon + Jeonghyun + Router)
- Goal: Leave enough context so another AI can continue immediately without re-discovery.

## 1) User Intent History (Chronological)

1. Read current folder and list files required to run project.
2. Extend analysis to all team folders (Huiseung/Jaewon/Jeonghyun), not only A.
3. Build integrated architecture documentation.
4. Start LangGraph-style Router integration after planning discussion.
5. Adopt Option B: create independent `Router/` package at repo root.
6. Keep LUXIA as mock first, define schemas/interfaces first, then connect real API later.
7. Execute both:
   - Split Job/Resume as importable service modules.
   - Connect FastAPI `/ask` route end-to-end through Router.

## 2) Key Deliverables Completed

### A. Cross-team architecture documentation
- Created/expanded:
  - `docs/YouthPath_architecture.md`
- Includes unified architecture and flow across:
  - Policy agent (A)
  - Job agent (Huiseung)
  - Resume agent (Jeonghyun)
  - API/UI layer (Jaewon)
  - New Router orchestration layer

### B. New Router package scaffold (Option B)
Created under `Router/`:
- `Router/__init__.py`
- `Router/__main__.py`
- `Router/main.py`
- `Router/schemas.py`
- `Router/llm_provider.py`
- `Router/formatters.py`
- `Router/agents.py`
- `Router/router.py`
- `Router/README.md`

### C. Job/Resume service separation for Router imports
Created:
- `Router/job_service.py`
- `Router/resume_service.py`

Updated:
- `Router/agents.py`
  - `run_job_agent` now uses `job_service`
  - `run_resume_agent` now uses `resume_service`

Current behavior:
- Job and Resume services are functional mock-style wrappers designed for Router integration.
- Full production linkage to original team pipelines is still pending.

### D. FastAPI `/ask` integration to Router
Updated:
- `YouthPath-jaewon/YouthPath-jaewon/main.py`
  - Replaced dummy response flow with Router invocation.
  - Added request field handling including `user_id`.

Updated:
- `YouthPath-jaewon/YouthPath-jaewon/app.py`
  - Streamlit now sends POST payload to `/ask` (instead of GET-like test flow).
  - Payload includes profile/context fields for Router.

### E. Job/Resume/Policy E2E hardening after LUXIA deferral
Updated:
- `Router/job_service.py`
  - Attempts Worknet live 채용정보/직무정보 pipeline first.
  - Falls back to the deterministic sample dataset when API/network/schema readiness fails.
  - Normalizes multiple likely Worknet response field names into the Router job schema.
- `Router/resume_service.py`
  - Attempts Jeonghyun DART/Naver async pipeline by dynamically loading `YouthPath-Jeonghyun/YouthPath-Jeonghyun/app.py`.
  - Normalizes Jeonghyun output into the Router `AgentResult` envelope.
  - Falls back to rule-based resume context when optional heavy deps/API readiness are missing.
- `Router/agents.py`
  - Wraps agent calls so one backend failure does not break the whole `/ask` response.
  - Implements real calendar deadline merge from policy/job outputs.
- `Router/llm_provider.py`
  - Keeps LUXIA mocked by default, but mock classification is now keyword-based instead of always `policy+job`.
  - Adds `LuxiaProvider` and `get_llm_provider()` so real LUXIA can be enabled by `.env` only.
  - Supports `openai`-style `messages` payloads and a `generic` `{prompt}` payload fallback.
- `YouthPath-jaewon/YouthPath-jaewon/main.py`, `Router/main.py`
  - Use `YouthPathRouter()` with provider auto-selection instead of hardcoding `MockLuxiaProvider`.
- `.env`
  - Adds commented LUXIA configuration template.

### F. Repository usage documentation and push preparation
Updated:
- `README.md`
  - Added current status, project layout, `.env` setup, E2E verification, Router-only run, FastAPI backend run, Streamlit frontend run, and LUXIA switch instructions.
- `docs/YouthPath_architecture.md`
  - Current status reflects the ready-to-switch LUXIA provider adapter.
- `worklog.md`
  - Current handoff notes updated for continuation and branch push.
- `A/services/policy_service.py`
  - Adds local `A/data/policies/*.json` fallback for policy-branch E2E when API/RAG dependencies are unavailable.
- `tmp_verify_e2e.py`
  - Adds a second scenario for `policy+job+resume+calendar`.

## 3) Runtime Verification Status

### Confirmed successful checks
1. Router import smoke test succeeded (`router-ok`).
2. Jaewon FastAPI module import succeeded; app title resolved as `YouthPath API`.
3. Required web stack packages were installed in venv (FastAPI/Streamlit/requests and dependencies).
4. File-based `/ask` E2E verification succeeded via `tmp_verify_e2e.py`.
    - Command: `& "c:/Users/hohoh/Documents/HanYang University/4-1/딥러닝및응용/project/.venv/Scripts/python.exe" "tmp_verify_e2e.py"`
    - Output summary:
       - `answer`: `[E2E-OK] Router merged job/resume results successfully.`
       - `counts`: `policy=0`, `job=2`, `resume=1`, `calendar=0`
       - response keys: `answer`, `policy`, `job`, `resume`, `calendar`, `metadata`, `error`
5. Policy-inclusive E2E verification succeeded via extended `tmp_verify_e2e.py`.
    - Output summary:
       - `answer`: `[E2E-OK] Router merged policy/job/resume/calendar results successfully.`
       - `counts`: `policy=7`, `job=2`, `resume=1`, `calendar=6`
       - response keys: `answer`, `policy`, `job`, `resume`, `calendar`, `metadata`, `error`

### Not fully finalized yet
- Production-grade E2E still depends on real LUXIA, confirmed Worknet endpoint contracts, and Resume optional dependencies/API keys.
- In the current dev environment, Resume live pipeline falls back because `OpenDartReader` is not installed.

## 4) Known Technical Decisions

1. Router architecture remains independent from team subprojects (root-level `Router/`).
2. LLM provider abstraction first:
   - `LLMProvider` interface exists.
   - `MockLuxiaProvider` is the default.
   - `LuxiaProvider` is ready and selected when `YOUTHPATH_LLM_PROVIDER=luxia`, `LUXIA_API_URL`, and `LUXIA_API_KEY` are set.
3. Common agent result envelope maintained via schema:
   - `agent_name`, `items`, `sources`, `metadata`, `error`
4. Policy path can rely on A services (`A.services.policy_service`) and may require environment/dependency readiness.
5. Job/Resume now attempt real team pipelines first and retain deterministic fallback paths for Router E2E.

## 5) Important Risks / Blockers

1. Real API coupling is partially wired but still environment/contract-dependent:
   - Job: Worknet live path is attempted, but endpoint/field contract should be confirmed with actual API docs.
   - Resume: DART/Naver pipeline is dynamically connected, but optional dependencies/API keys must be installed for live execution.
2. Real LUXIA live use pending:
   - Provider adapter exists.
   - Need issued endpoint/key and final request-response contract confirmation.
3. Environment mismatch risk:
   - `.env` contains keys, but runtime process may not load/export them depending on launch path.
4. Repository is currently dirty with many changed files (including many policy JSON files under A/data).
   - Do not revert unrelated changes blindly.

## 6) Recommended Immediate Next Steps (for next AI)

1. Confirm Worknet endpoint/path/field names against the official Work24 OpenAPI docs.

2. Install/verify Resume live dependencies (`OpenDartReader`, `chromadb`, `sentence_transformers`, `keybert`) and API keys, then rerun E2E.

3. Enable LUXIA by `.env` after API contract is available.
   - Set `YOUTHPATH_LLM_PROVIDER=luxia`, `LUXIA_API_URL`, `LUXIA_API_KEY`.
   - Adjust `LUXIA_REQUEST_FORMAT` to `openai` or `generic`.

4. Re-run API route E2E using Jaewon backend + frontend flow.
   - Validate request schema from Streamlit to FastAPI.
   - Validate Router branch selection and merged response rendering.

## 7) Quick Handoff Checklist

- [x] Router package exists and imports.
- [x] FastAPI `/ask` is Router-connected.
- [x] Streamlit sends POST payload.
- [x] Job/Resume wrapper modules separated.
- [x] File-based stable E2E proof output captured.
- [x] Policy-inclusive E2E proof output captured.
- [x] Real Job pipeline attempted first with fallback.
- [x] Real Resume pipeline attempted first with fallback.
- [x] Real LUXIA provider adapter wired.
- [ ] Real LUXIA endpoint/key live-verified.
- [x] Root README usage guide written.

## 8) Suggested Validation Commands (Windows, venv context)

Note: run from project root with activated venv.

```powershell
# Router import smoke test
python -c "from Router.router import YouthPathRouter; print('router-ok')"

# FastAPI module import check (Jaewon)
python -c "import sys; sys.path.append('YouthPath-jaewon/YouthPath-jaewon'); import main; print(main.app.title)"
```

For full E2E, prefer a temporary script file instead of one-liner due to quoting/path issues on this environment.

## 9) Files Most Relevant for Continuation

- Router core:
  - `Router/router.py`
  - `Router/agents.py`
  - `Router/job_service.py`
  - `Router/resume_service.py`
  - `Router/llm_provider.py`
  - `Router/schemas.py`
- API/UI integration:
  - `YouthPath-jaewon/YouthPath-jaewon/main.py`
  - `YouthPath-jaewon/YouthPath-jaewon/app.py`
- Policy integration source:
  - `A/services/policy_service.py`
- Architecture reference:
  - `docs/YouthPath_architecture.md`

## 10) Notes for Safe Continuation

1. Preserve existing response schema contracts unless explicitly changing all consumers.
2. Keep mock provider path available while integrating real APIs.
3. Validate in small steps:
   - import -> route call -> single-agent -> multi-agent merge -> frontend render.
4. If runtime import fails, check sys.path and package working directory before code edits.

## 11) Module Import Fix (2026-06-02)

### Issue
When running FastAPI backend from `YouthPath-jaewon/YouthPath-jaewon/` subdirectory, uvicorn failed with:
```
ModuleNotFoundError: No module named 'Router'
```

The issue occurred because `main.py` imports `from Router.router import YouthPathRouter`, but the `Router/` package is at the project root, not relative to the script's working directory.

### Fix Applied
Updated `YouthPath-jaewon/YouthPath-jaewon/main.py`:
- Added `sys.path` manipulation at module import time to include project root.
- Located project root dynamically using `Path(__file__).parent.parent.parent`.
- This ensures `Router` module is discoverable regardless of launch directory.

**Change:**
```python
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from Router.router import YouthPathRouter
```

### Verification
Ran FastAPI backend via the recommended setup:
```powershell
cd YouthPath-jaewon\YouthPath-jaewon
..\..\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

**Result:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [42484] using WatchFiles
INFO:     Started server process [33672]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Server is now running and ready for FastAPI requests.

## 12) LUXIA `.env` Loading Fix (2026-06-02)

### Issue
FastAPI was commonly launched from `YouthPath-jaewon/YouthPath-jaewon/`, while `Router/llm_provider.py` only loaded:
```python
Path.cwd() / ".env"
```

Because the real `.env` file is at the project root, `YOUTHPATH_LLM_PROVIDER`, `LUXIA_API_URL`, and `LUXIA_API_KEY` were not loaded in that launch mode. As a result, `get_llm_provider()` selected `MockLuxiaProvider`, and API output showed:
```json
"llm_provider": "MockLuxiaProvider"
```

### Fix Applied
Updated `Router/llm_provider.py` so `_load_env_file()` checks both:
- current working directory `.env`
- project root `.env` resolved relative to `Router/llm_provider.py`

### Verification
From `YouthPath-jaewon/YouthPath-jaewon/`, importing the real FastAPI entrypoint now selects:
```text
LuxiaProvider
True
luxia3-llm-32b-0731
```

This confirms the provider selection now sees the root `.env`. Full live LUXIA response verification is still separate because it requires making a real API request.
