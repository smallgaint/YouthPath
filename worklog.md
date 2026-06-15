# WORKLOG

- Last updated: 2026-06-14
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
- Production-grade E2E still depends on confirmed Worknet endpoint contracts, Worknet live key verification, and Resume optional dependencies/API keys.
- In the current dev environment, Resume live pipeline falls back because `OpenDartReader` is not installed.

## 4) Known Technical Decisions

1. Router architecture remains independent from team subprojects (root-level `Router/`).
2. LLM provider abstraction first:
   - `LLMProvider` interface exists.
   - `MockLuxiaProvider` is the default.
   - `LuxiaProvider` is selected when `YOUTHPATH_LLM_PROVIDER=luxia`, `LUXIA_API_URL`, and `LUXIA_API_KEY` are set.
   - Real LUXIA was live-verified on 2026-06-14 with the `apikey` header and `/luxia/v1/chat` endpoint.
3. Common agent result envelope maintained via schema:
   - `agent_name`, `items`, `sources`, `metadata`, `error`
4. Policy path can rely on A services (`A.services.policy_service`) and may require environment/dependency readiness.
5. Job/Resume now attempt real team pipelines first and retain deterministic fallback paths for Router E2E.

## 5) Important Risks / Blockers

1. Real API coupling is partially wired but still environment/contract-dependent:
   - Job: Worknet live path is attempted, but endpoint/field contract should be confirmed with actual API docs.
   - Resume: DART/Naver pipeline is dynamically connected, but optional dependencies/API keys must be installed for live execution.
2. Real LUXIA live use is no longer pending:
   - Provider adapter exists.
   - Endpoint/key/request format were confirmed by live smoke test on 2026-06-14.
   - Current remaining risk is latency and model availability, especially with `luxia3-llm-32b-0731`.
3. Environment mismatch risk:
   - `.env` contains keys, but runtime process may not load/export them depending on launch path.
4. Repository is currently dirty with many changed files (including many policy JSON files under A/data).
   - Do not revert unrelated changes blindly.

## 6) Recommended Immediate Next Steps (for next AI)

1. Confirm Worknet endpoint/path/field names against the official Work24 OpenAPI docs.

2. Install/verify Resume live dependencies (`OpenDartReader`, `chromadb`, `sentence_transformers`, `keybert`) and API keys, then rerun E2E.

3. Keep LUXIA enabled through `.env` when real LLM behavior is needed.
   - Set `YOUTHPATH_LLM_PROVIDER=luxia`, `LUXIA_API_URL`, `LUXIA_API_KEY`.
   - Use `LUXIA_AUTH_HEADER=apikey`, `LUXIA_AUTH_SCHEME=`, and `LUXIA_TIMEOUT=60`.

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
- [x] Real LUXIA endpoint/key live-verified.
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

## 13) Full Integration State and Code Connection Map (2026-06-14)

### Purpose
This section records the integration work from the first cross-team merge through the current live-API wiring, so a future maintainer can understand the project by reading this worklog alone.

The integration goal was:
- keep each member's original project code available,
- add a root-level orchestration layer,
- expose one FastAPI `/ask` endpoint,
- let Streamlit call that endpoint,
- route one user query into policy/job/resume/calendar agents,
- merge structured agent results with one natural-language LLM answer.

### Repository-Level Architecture
The project is now organized around these boundaries:

- `Router/`
  - Root-level orchestration package.
  - Owns request routing, agent selection, result normalization, LLM provider selection, formatting, and fallback handling.
- `A/`
  - Policy agent source and local policy data fallback.
  - Router policy wrapper calls this path when policy intent is selected.
- `YouthPath-Huiseung/`
  - Original Job Agent / Worknet reference implementation.
  - Router currently uses `Router/job_service.py` as the importable service wrapper for job results.
- `YouthPath-Jeonghyun/`
  - Resume/DART/Naver reference pipeline.
  - Router uses `Router/resume_service.py` to attempt dynamic loading of the original pipeline and falls back when optional dependencies/API keys are missing.
- `YouthPath-jaewon/YouthPath-jaewon/`
  - FastAPI + Streamlit user-facing layer.
  - `main.py` exposes `/ask`; `app.py` and `app_proto.py` call `/ask`.

### Router Flow
Main runtime flow:

1. Frontend sends a POST request to `http://127.0.0.1:8000/ask`.
2. `YouthPath-jaewon/YouthPath-jaewon/main.py` receives the request through FastAPI.
3. `main.py` creates/uses `YouthPathRouter()` from `Router/router.py`.
4. `YouthPathRouter.invoke()` coerces the request into `RouterRequest`.
5. Router builds a classification prompt.
6. Router calls the configured LLM provider through `LLMProvider.invoke()`.
7. Classification output is parsed as JSON:
   - expected shape: `{"agents": ["policy", "job", "resume", "calendar"], "reasoning": "..."}`
8. Router runs only the selected agent wrappers:
   - `run_policy_agent`
   - `run_job_agent`
   - `run_resume_agent`
   - `run_calendar_agent`
9. Each agent returns the shared `AgentResult` envelope:
   - `agent_name`
   - `items`
   - `sources`
   - `metadata`
   - `error`
10. Router formats structured agent outputs into text using `Router/formatters.py`.
11. Router sends a final synthesis prompt to the LLM provider.
12. Router returns a JSON response with:
   - `answer`
   - `policy`
   - `job`
   - `resume`
   - `calendar`
   - `metadata`
   - `error`

### Files Modified During Core Integration

#### `Router/router.py`
- Created the core `YouthPathRouter` class.
- Added request coercion so callers can pass either a `RouterRequest` object or a plain dict.
- Added classification prompt generation.
- Added agent selection normalization.
- Added final prompt generation.
- Added metadata fields:
  - `classification`
  - `agents_called`
  - `llm_provider`
  - `latency_ms`
  - `agent_errors`

#### `Router/schemas.py`
- Created shared dataclasses/schemas for router and agent communication.
- Standardized response envelopes so frontend rendering does not need to know each team's internal format.

#### `Router/agents.py`
- Added wrapper functions for policy/job/resume/calendar.
- Wrapped backend calls so one failing agent does not break the entire `/ask` response.
- Added calendar merge logic from policy/job deadlines.

#### `Router/formatters.py`
- Added text-formatting helpers for policy/job/resume/calendar results.
- These formatted strings are inserted into the final LLM synthesis prompt.

#### `Router/job_service.py`
- Separated Job Agent behavior into an importable service.
- Attempts Worknet live search first.
- Normalizes likely Worknet response field names into the Router job schema.
- Computes lightweight fit score from profile/skills/region/deadline/career.
- Falls back to deterministic sample job data if Worknet call fails or returns no usable rows.

#### `Router/resume_service.py`
- Separated Resume Agent behavior into an importable service.
- Attempts Jeonghyun's original async DART/Naver pipeline through dynamic loading.
- Normalizes output into Router schema.
- Falls back to rule-based resume guidance when optional dependencies or API keys are not ready.

#### `Router/llm_provider.py`
- Created `LLMProvider` abstract interface.
- Created `MockLuxiaProvider` for stable local E2E.
- Created `LuxiaProvider` for real Luxia API calls.
- Added `get_llm_provider()` so provider selection comes from `.env`.
- Added root `.env` loading even when FastAPI is launched from the Jaewon subdirectory.

#### `YouthPath-jaewon/YouthPath-jaewon/main.py`
- Added project-root `sys.path` handling so `Router` can be imported from subdirectory launch modes.
- Replaced dummy FastAPI `/ask` response with `YouthPathRouter.invoke()`.
- Kept the FastAPI app title as `YouthPath API`.
- Added/kept CORS for Streamlit integration.

#### `YouthPath-jaewon/YouthPath-jaewon/app.py`
- Updated Streamlit frontend flow to send POST JSON to `/ask`.
- Added profile fields into the request payload.
- Renders Router response sections for natural-language answer, policy, job, resume, and calendar outputs.

#### `YouthPath-jaewon/YouthPath-jaewon/app_proto.py`
- Added a lightweight prototype Streamlit client for quick `/ask` testing.
- Sends a compact profile/query payload to the FastAPI backend.

#### `README.md` and `Router/README.md`
- Documented project layout, run commands, env setup, Router behavior, and LUXIA/Worknet configuration.

### Validation History
Stable validation steps used during integration:

- Router import smoke test:
```powershell
python -c "from Router.router import YouthPathRouter; print('router-ok')"
```

- FastAPI import smoke test:
```powershell
python -c "import sys; sys.path.append('YouthPath-jaewon/YouthPath-jaewon'); import main; print(main.app.title)"
```

- File-based E2E:
```powershell
python tmp_verify_e2e.py
```

Confirmed E2E shapes:
- `job+resume`: Router returns answer + job + resume with no policy/calendar.
- `policy+job+resume+calendar`: Router returns all major arrays and merged calendar deadlines.

## 14) Real LUXIA Request Form Fix and Live Verification (2026-06-14)

### Problem
The project had received a real Luxia API key and `.env` values were filled, but real LLM calls still failed.

Root cause:
- The previous `LuxiaProvider` default header was OpenAI-style:
```text
Authorization: Bearer <key>
```
- Luxia documentation requires:
```text
apikey: <key>
Content-Type: application/json
```
- The previous payload also included optional generation fields by default, while the official Luxia examples showed the minimal chat body:
```json
{
  "model": "luxia3-llm-32b-0731",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}
```

### Code Changes
Updated `Router/llm_provider.py`:

- Changed default auth header:
```python
self.auth_header = os.getenv("LUXIA_AUTH_HEADER", "apikey").strip()
```

- Removed default auth scheme:
```python
self.auth_scheme = os.getenv("LUXIA_AUTH_SCHEME", "").strip()
```

- Added official Luxia stream flag:
```python
"stream": False
```

- Added opt-in generation parameters:
```python
self.include_generation_params = (
    os.getenv("LUXIA_INCLUDE_GENERATION_PARAMS", "false").strip().lower() == "true"
)
```

- Only includes `temperature` and `max_tokens` when:
```env
LUXIA_INCLUDE_GENERATION_PARAMS=true
```

- Increased default timeout to 60 seconds:
```python
self.timeout = timeout or float(os.getenv("LUXIA_TIMEOUT", "60"))
```

Updated `.env` locally:
```env
YOUTHPATH_LLM_PROVIDER="luxia"
LUXIA_API_URL="https://bridge.luxiacloud.com/luxia/v1/chat"
LUXIA_MODEL="luxia3-llm-32b-0731"
LUXIA_TIMEOUT=60
LUXIA_REQUEST_FORMAT="openai"
LUXIA_AUTH_HEADER="apikey"
LUXIA_AUTH_SCHEME=""
LUXIA_INCLUDE_GENERATION_PARAMS=false
LUXIA_FALLBACK_TO_MOCK=false
```

### Verification
A temporary smoke script was created and then removed after testing.

The first live request succeeded but printing the Korean response failed because Windows console encoding was `cp1252`.

The print output was changed to ASCII-safe JSON escaping, then the live request was retried.

Observed successful response:
```json
{"response": "\ub300\ud55c\ubbfc\uad6d\uc758 \uc218\ub3c4\ub294 \uc11c\uc6b8\uc785\ub2c8\ub2e4."}
```

Decoded response:
```text
대한민국의 수도는 서울입니다.
```

Observed latency:
- about 18 seconds with `luxia3-llm-32b-0731`

Conclusion:
- LUXIA endpoint/key/request format are live-verified.
- The earlier blocker was request form/auth header mismatch, plus timeout needed to be more generous for 32B.

## 15) Main Branch Push After LUXIA/App State Update (2026-06-14)

### Requested Action
User requested the current local state be pushed to `main`.

### Initial State
Local branch:
```text
A
```

Remote tracking:
```text
youthpath/A
```

Target remote branch:
```text
youthpath/main
```

Files staged/committed in that push included:
- `README.md`
- `Router/README.md`
- `Router/llm_provider.py`
- `YouthPath-jaewon/YouthPath-jaewon/app.py`
- `YouthPath-jaewon/YouthPath-jaewon/app_proto.py`
- `YouthPath-jaewon/YouthPath-jaewon/frontend/app.py` deletion
- `YouthPath-jaewon/YouthPath-jaewon/main.py`
- `worklog.md`

### Commit Created
```text
12ce909 Update YouthPath Luxia integration and app state
```

Stats:
```text
8 files changed, 683 insertions(+), 580 deletions(-)
create mode 100644 YouthPath-jaewon/YouthPath-jaewon/app_proto.py
delete mode 100644 YouthPath-jaewon/YouthPath-jaewon/frontend/app.py
```

### Push Attempt and Resolution
First push command:
```powershell
git push youthpath HEAD:main
```

Result:
```text
rejected: non-fast-forward
```

Reason:
- `youthpath/main` had remote commits not present locally.

Resolution:
```powershell
git fetch youthpath main
git merge youthpath/main
git push youthpath HEAD:main
```

Merge result:
```text
bf4fadd Merge remote-tracking branch 'youthpath/main' into A
```

Remote main moved:
```text
ceb0525..bf4fadd  HEAD -> main
```

Remote main push succeeded.

Note:
- Local branch remained `A`.
- After push, local `A` was ahead of `youthpath/A`; main push was successful, but `A` itself was not pushed as `A`.

## 16) Worknet API Key Environment Wiring (2026-06-14)

### Problem
The Job Agent had Worknet API keys hardcoded as default values in `Router/job_service.py`.

Previous pattern:
```python
WORKNET_KEYS = {
    "채용정보": os.getenv("WORKNET_RECRUIT_API_KEY", "<hardcoded-default-key>"),
    ...
}
```

Problems:
- Secrets/default keys should not live in source code.
- A user filling `.env` should be the only supported way to configure live Worknet.
- If no key is configured, the app should still run through mock fallback instead of making invalid live calls.

### Code Changes
Updated `Router/job_service.py`:

- Added local `.env` loader matching the LUXIA provider behavior:
```python
def _load_env_file() -> None:
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    ...
```

- Added shared key fallback helper:
```python
def _worknet_key(env_name: str) -> str:
    return (os.getenv(env_name) or os.getenv("WORKNET_API_KEY") or "").strip()
```

- Changed `WORKNET_KEYS` to read only env values:
```python
WORKNET_KEYS = {
    "채용정보": _worknet_key("WORKNET_RECRUIT_API_KEY"),
    "강소기업": _worknet_key("WORKNET_SME_API_KEY"),
    "직무정보": _worknet_key("WORKNET_JOB_INFO_API_KEY"),
    "공통코드": _worknet_key("WORKNET_COMMON_CODE_API_KEY"),
    "직업정보": _worknet_key("WORKNET_OCCUPATION_API_KEY"),
}
```

- Added Worknet timeout env:
```python
WORKNET_TIMEOUT = float(os.getenv("WORKNET_TIMEOUT", "6"))
```

- Added explicit live-search guard:
```python
if not WORKNET_KEYS["채용정보"]:
    raise ValueError("WORKNET_RECRUIT_API_KEY or WORKNET_API_KEY is required for Worknet live search.")
```

This exception is caught in `run_job_agent()`, so the service falls back to the deterministic mock Worknet sample data.

- Added job-skill API guard:
```python
if not WORKNET_KEYS["직무정보"]:
    return fallback
```

### Local `.env` Shape Added
The local `.env` now includes:

```env
# Worknet API integration
# If one Worknet authKey can be reused across endpoints, fill only WORKNET_API_KEY.
# If Worknet issues endpoint-specific keys, fill the specific keys below instead.
WORKNET_API_KEY=""
WORKNET_RECRUIT_API_KEY=""
WORKNET_JOB_INFO_API_KEY=""
WORKNET_SME_API_KEY=""
WORKNET_COMMON_CODE_API_KEY=""
WORKNET_OCCUPATION_API_KEY=""
WORKNET_TIMEOUT=6
```

Recommended user input:

If one Worknet `authKey` works for all endpoints:
```env
WORKNET_API_KEY="발급받은_워크넷_authKey"
```

If Worknet gives endpoint-specific keys:
```env
WORKNET_RECRUIT_API_KEY="채용정보_authKey"
WORKNET_JOB_INFO_API_KEY="직무정보_authKey"
WORKNET_SME_API_KEY="강소기업_authKey"
WORKNET_COMMON_CODE_API_KEY="공통코드_authKey"
WORKNET_OCCUPATION_API_KEY="직업정보_authKey"
```

### Documentation Changes
Updated `README.md` with the same Worknet env format and explanation.

### Verification
Completed:
```powershell
python -m compileall Router
```

Result:
- Passed.
- `Router/job_service.py` compiled successfully.

Not completed:
- Runtime fallback test was proposed, but the user rejected the escalated command request.
- Therefore only syntax/import compilation was verified for this step.

## 17) Current Status After 2026-06-14 Changes

### Completed
- Root Router package exists and is the central integration point.
- FastAPI `/ask` is connected to Router.
- Streamlit app posts JSON to `/ask`.
- Policy/job/resume/calendar response schema is unified.
- Job and Resume services have live-first/fallback behavior.
- LUXIA real API call is live-verified with `apikey` header and official `/luxia/v1/chat` endpoint.
- Worknet keys are no longer hardcoded in source.
- Worknet now reads from root `.env`.
- README explains LUXIA and Worknet env setup.
- Current integrated state was pushed to `youthpath/main` at merge commit `bf4fadd`.

### Still Needs Attention
- Worknet live endpoint behavior should be tested after the user fills a real `WORKNET_API_KEY`.
- Resume live path still depends on optional dependencies/API keys such as DART/Naver-related packages.
- Full backend + frontend live E2E should be rerun after Worknet key insertion.
- `.env` is local and should not be committed with real secrets.

### Suggested Next Validation Order
1. Fill `.env`:
```env
WORKNET_API_KEY="actual-worknet-auth-key"
```

2. Run Router compile check:
```powershell
python -m compileall Router
```

3. Start backend:
```powershell
cd YouthPath-jaewon\YouthPath-jaewon
..\..\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

4. Send a job-focused request to `/ask`:
```json
{
  "query": "서울 데이터 분석 신입 채용 알려줘",
  "profile": {
    "age": 27,
    "region": "서울",
    "skills": ["Python", "SQL"],
    "target_role": "데이터 분석가",
    "experience_y": 0
  },
  "user_id": "debug"
}
```

5. Check response metadata:
```json
"metadata": {
  "agents_called": ["job"],
  ...
}
```

6. In the job agent metadata, confirm whether backend is:
```json
"backend": "worknet"
```

If backend is still `mock`, inspect:
- `metadata.agent_errors`
- Worknet HTTP status/response shape
- whether the entered key belongs to the correct Worknet OpenAPI service
