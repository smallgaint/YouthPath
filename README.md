# 1. Branch Purpose
This branch implements the first version of the **Resume Agent** for the YouthPath project.
The Resume Agent does not generate the final answer with an LLM.  
Instead, it creates a structured context that can later be consumed by the integrated LLM/router.

## Current responsibility of this branch:
```text
User profile
→ DART disclosure Static RAG
→ Naver News Dynamic RAG
→ KeyBERT keyword extraction
→ User skill/company keyword matching
→ Context JSON save
```
The final natural-language response generation is delegated to the integrated LLM/router.

# 2. Current Implementation Summary

## Main file:
```text
app.py
```
## Current pipeline:
```text
1. Load environment variables from .env
2. Load local embedding model: jhgan/ko-sroberta-multitask
3. Initialize KeyBERT with the same embedding model
4. Load ChromaDB collection: companies
5. Check whether target company is already indexed
6. If company is not indexed, fetch DART disclosures and store chunks into ChromaDB
7. Retrieve DART disclosure chunks from ChromaDB
8. Merge retrieved chunks
9. Extract company keywords using KeyBERT
10. Normalize/filter extracted keywords
11. Match user skills with company keywords using cosine similarity
12. Fetch latest news from Naver News API
13. Save the final Resume Agent context as JSON
```
--
# 3. Input / Output

## Test Input
Currently, user input is hardcoded in main() for testing.

```text
test_profile = {
    "target_company": "네이버",
    "company_identifier": "035420",
    "target_role": "AI 엔지니어",
    "skills": [
        "LLM 기반 RAG 시스템 개발",
        "ChromaDB 기반 벡터 검색",
        "FastAPI 비동기 처리",
        "Docker 컨테이너화",
        "Vision-Language Model 활용",
        "보험 약관 문서 자동화",
        "Python",
        "SQL"
    ]
}
```
Later, this part should be replaced with Streamlit/FastAPI input.

## Output
The agent saves output JSON files under:
agent_outputs/

Example:

```text
agent_outputs/resume_context_네이버_YYYYMMDD_HHMMSS.json
```
Output format:
```text
{
  "agent_name": "resume",
  "items": [
    {
      "company": "네이버",
      "company_identifier": "035420",
      "emphasize_keywords": [],
      "matching_points": [],
      "evidence_gaps": [],
      "story_angles": [],
      "dynamic_news": [],
      "static_disclosure_chunks": [],
      "retrieved_chunk_count": 15
    }
  ],
  "context_text": "...",
  "sources": [
    "ChromaDB companies",
    "DART disclosure chunks",
    "Naver News API"
  ],
  "metadata": {
    "llm_used": false,
    "created_at": "...",
    "note": "Final answer generation is delegated to the integrated LLM/router."
  },
  "error": null
}
```
--
# 4. Environment Variables

Create a local .env file based on .env.template.

Required variables:

DART_API_KEY=your_dart_api_key_here
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=companies

Do not commit .env.

-- 
# 5. How to Run

Activate virtual environment:
```text
source /Users/irenekang/YouthPath/.venv/bin/activate
```
Install dependencies:
```text
python -m pip install -r requirements.txt
```
Run the agent:
```text
python app.py
```
Important: use python app.py, not python3 app.py.

--
# 6. Current Test Result

Current tested company:
```text
네이버 / 035420
```
Confirmed working:
```text
DART Static RAG ✅
- Existing ChromaDB disclosure vectors loaded
- Company metadata loaded from ChromaDB
- DART disclosure chunks retrieved
Naver Dynamic RAG ✅
- Naver News API returned status_code 200
- Latest news titles and links collected
KeyBERT Keyword Extraction ✅
- Company keywords extracted from DART disclosure chunks
- Keyword normalization/filtering applied
User Matching ✅
- User skills matched with extracted company keywords using cosine similarity
Context Save ✅
- Resume Agent context saved as JSON under agent_outputs/
```
-- 
# 7. Current Limitations

## 1. Keyword quality still needs improvement

Examples of noisy outputs:
```text
인터넷 운영과정에서 축적된
성장하고 디스플레이는
높은 기여를 있을
랩스 서비스별
```
This can be improved by updating:
```text
is_valid_keyword()
normalize_keyword()
preprocess_text_for_keybert()
```

## 2. DART indexing and agent execution are still in one file

Currently, app.py contains both:
- DART disclosure ingestion
- Resume Agent execution

Future Structure:
```text
ingest_disclosures.py
→ DART API fetch
→ chunking
→ ChromaDB save

resume_agent.py
→ ChromaDB search
→ KeyBERT extraction
→ Naver News API
→ matching
→ context JSON return
```
--
# 8. Files Should be ignored:
```text
.env
chroma_db/
agent_outputs/
disclosure_data/
docs_cache/
__pycache__/
*.pyc
.DS_Store
```
--
# 9. Suggested Next Tasks

1. Split app.py into separate modules:
    * ingest_disclosures.py
    * resume_agent.py
    * utils.py
2. Improve KeyBERT post-processing:
    * Add more banned tokens
    * Add more normalization mappings
    * Remove sentence-like keywords
3. Replace hardcoded test_profile with Streamlit/FastAPI input.
4. Decide shared agent output schema with other team members.
5. Connect this agent output to the integrated LLM/router.

-- 
# 10. Branch Status
purpose: Resume agent 1st commit

This branch is ready for team review as a first working prototype of:
DART Static RAG + Naver Dynamic RAG + KeyBERT + user matching + JSON context save
