import os
import re
import json
import asyncio
import hashlib
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import httpx
import chromadb
import OpenDartReader

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT


# ============================================================
# 1. 환경 변수 로드
# ============================================================
load_dotenv()

DART_API_KEY = os.getenv("DART_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "companies")

if not DART_API_KEY:
    raise ValueError("DART_API_KEY가 없습니다. .env 파일을 확인하세요.")

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


# ============================================================
# 2. 모델 로드
# ============================================================
# print("📥 임베딩 모델 로드 중")
embedding_model = SentenceTransformer("jhgan/ko-sroberta-multitask")

# print("🔑 KeyBERT 초기화 중")
keyword_model = KeyBERT(model=embedding_model)


# ============================================================
# 3. 공통 유틸
# ============================================================
def calculate_cosine_similarity(vec1, vec2) -> float:
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)

    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0

    return float(dot_product / (norm_vec1 * norm_vec2))


def clean_html_text(raw_html: str) -> str:
    """
    DART document HTML/XML을 일반 텍스트로 정제.
    """
    if not raw_html:
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """
    긴 공시 본문을 임베딩 가능한 청크로 분할.
    """
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if len(chunk) > 100:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def make_stable_id(company_name: str, rcept_no: str, idx: int, chunk: str) -> str:
    raw = f"{company_name}_{rcept_no}_{idx}_{chunk[:50]}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def load_companies_collection():
    """
    ChromaDB companies 컬렉션 로드.
    """
    print(f"🗄️ ChromaDB 로드: {CHROMA_DB_PATH} / {CHROMA_COLLECTION_NAME}")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
    return collection


def check_company_indexed(collection, company_name: str) -> bool:
    """
    profile.target_company가 사전 인덱싱된 기업인지 확인.
    """
    result = collection.get(
        where={"company_name": company_name},
        limit=1,
        include=["metadatas"]
    )

    return len(result.get("ids", [])) > 0


def get_company_metadata(collection, company_name: str) -> dict | None:
    """
    ChromaDB metadata에서 company_identifier 등 기업 정보를 가져옴.
    """
    result = collection.get(
        where={"company_name": company_name},
        limit=1,
        include=["metadatas"]
    )

    metadatas = result.get("metadatas", [])

    if not metadatas:
        return None

    return metadatas[0]


# ============================================================
# 4. DART 공시 수집 + VectorDB 저장
# ============================================================
class DartDisclosureVectorBuilder:
    """
    DART API에서 실제 공시를 가져와 ChromaDB companies 컬렉션에 저장하는 모듈.

    원칙적으로는 사전 인덱싱 단계에서 실행.
    app.py 테스트에서는 ChromaDB에 기업이 없을 때 한 번 실행 가능.
    """

    def __init__(self):
        self.reader = OpenDartReader(DART_API_KEY)
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME
        )

    def fetch_disclosure_list(self, company_identifier: str, start_date: str) -> pd.DataFrame:
        print(f"📄 DART 공시 목록 수집 중: {company_identifier}, start={start_date}")

        df = self.reader.list(company_identifier, start=start_date)

        if df is None or df.empty:
            raise ValueError(f"{company_identifier}의 {start_date} 이후 공시가 없습니다.")

        os.makedirs("disclosure_data", exist_ok=True)
        save_path = f"disclosure_data/disclosures_{company_identifier}_{start_date}.csv"
        df.to_csv(save_path, index=False, encoding="utf-8-sig")

        print(f"✅ 공시 목록 저장 완료: {save_path}")
        return df

    def select_target_reports(self, disclosure_df: pd.DataFrame, max_reports: int = 3) -> pd.DataFrame:
        """
        사업보고서/반기보고서/분기보고서 중심으로 가져옴.
        """
        report_keywords = ["사업보고서", "반기보고서", "분기보고서"]

        target_df = disclosure_df[
            disclosure_df["report_nm"].astype(str).apply(
                lambda x: any(keyword in x for keyword in report_keywords)
            )
        ].copy()

        if target_df.empty:
            target_df = disclosure_df.copy()

        return target_df.head(max_reports)

    def fetch_report_text(self, rcept_no: str) -> str:
        """
        DART 접수번호 기반 공시 본문 수집.
        """
        try:
            raw_doc = self.reader.document(rcept_no)
            return clean_html_text(raw_doc)
        except Exception as e:
            print(f"⚠️ 공시 본문 수집 실패: rcept_no={rcept_no}, error={str(e)}")
            return ""

    def build_vector_db(self, company_identifier: str, company_name: str, start_date: str):
        """
        DART 공시 목록 수집 → 본문 수집 → chunking → embedding → ChromaDB upsert.
        """
        disclosure_df = self.fetch_disclosure_list(company_identifier, start_date)
        target_reports = self.select_target_reports(disclosure_df, max_reports=3)

        total_chunks = 0

        for _, row in target_reports.iterrows():
            report_name = str(row.get("report_nm", ""))
            rcept_no = str(row.get("rcept_no", ""))
            rcept_dt = str(row.get("rcept_dt", ""))
            corp_name = str(row.get("corp_name", company_name))

            print(f"🔎 공시 본문 수집 중: {report_name} / {rcept_no}")

            report_text = self.fetch_report_text(rcept_no)
            chunks = chunk_text(report_text)

            if not chunks:
                print(f"⚠️ 유효한 chunk 없음: {report_name}")
                continue

            ids = []
            documents = []
            embeddings = []
            metadatas = []

            for idx, chunk in enumerate(chunks):
                chunk_id = make_stable_id(company_name, rcept_no, idx, chunk)
                embedding = embedding_model.encode(chunk).tolist()

                ids.append(chunk_id)
                documents.append(chunk)
                embeddings.append(embedding)
                metadatas.append({
                    "company_name": company_name,
                    "company_identifier": company_identifier,
                    "corp_name": corp_name,
                    "report_name": report_name,
                    "rcept_no": rcept_no,
                    "rcept_dt": rcept_dt,
                    "source": "DART"
                })

            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            total_chunks += len(chunks)
            print(f"✅ VectorDB 저장 완료: {report_name}, chunks={len(chunks)}")

        print(f"🎯 전체 VectorDB 저장 완료: total_chunks={total_chunks}")
        return self.collection


# ============================================================
# 5. 네이버 뉴스 API Dynamic RAG
# ============================================================
async def fetch_naver_news(company_name: str):
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("⚠️ 네이버 API 키가 없어 뉴스 수집을 건너뜁니다.")
        return [{
            "title": "네이버 뉴스 API 키가 없어 최신 뉴스 수집을 수행하지 못했습니다.",
            "link": ""
        }]

    query = f"{company_name} AI 신사업 전략"
    url = "https://openapi.naver.com/v1/search/news.json"

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": query,
        "display": 5,
        "sort": "sim"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers=headers,
                params=params,
                timeout=5.0
            )

            if response.status_code != 200:
                print(f"⚠️ 네이버 뉴스 API 응답 오류: {response.status_code}")
                print(response.text[:300])
                return [{
                    "title": f"네이버 뉴스 API 호출 실패로 {company_name} 최신 뉴스 수집을 수행하지 못했습니다.",
                    "link": ""
                }]

            items = response.json().get("items", [])
            cleaned_news = []

            for item in items:
                title = re.sub(r"<[^>]+>", "", item.get("title", ""))
                title = title.replace("&quot;", '"').replace("&amp;", "&")
                link = item.get("link", "")

                if title:
                    cleaned_news.append({
                        "title": title,
                        "link": link
                    })

            return cleaned_news

        except Exception as e:
            print(f"⚠️ 네이버 뉴스 API 에러: {str(e)}")

    return [{
        "title": f"{company_name}의 최신 뉴스를 가져오지 못했습니다.",
        "link": ""
    }]


# ============================================================
# 6. Resume Agent 핵심 함수
# ============================================================
def retrieve_company_chunks(collection, company_name: str, k: int = 15):
    """
    Step 2. Chroma companies 벡터 컬렉션 검색.
    query='사업의 내용 R&D 인재상'
    filter={'company_name': company_name}
    """
    query_text = (
        f"{company_name} 사업의 내용 주요 제품 서비스 "
        "AI 클라우드 커머스 콘텐츠 검색 플랫폼 엔터프라이즈 "
        "신사업 성장전략 글로벌 기술 플랫폼"
    )
    query_embedding = embedding_model.encode(query_text).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where={"company_name": company_name}
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

    documents = [doc for doc in documents if doc]

    return documents, metadatas

def preprocess_text_for_keybert(text: str) -> str:
    """
    KeyBERT 입력 전 공시 원문 노이즈 제거.
    표/임원/조직도/반복 문구를 줄여 키워드 품질을 높인다.
    """
    if not text:
        return ""

    remove_patterns = [
        r"연구개발조직도\.jpg",
        r"연구개발조직도",
        r"요약현황은 다음과 같습니다",
        r"다음과 같습니다",
        r"당사는",
        r"상기",
        r"기준일 현재",
        r"보유주식수",
        r"상근",
        r"비상근",
        r"남\s*\d{4}년",
        r"여\s*\d{4}년",
        r"\d{4}년\s*\d{1,2}월~기준일 현재",
        r"[0-9,]+\s*-",
        r"ㆍ",
    ]

    cleaned = text

    for pattern in remove_patterns:
        cleaned = re.sub(pattern, " ", cleaned)

    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()

def is_valid_keyword(keyword: str) -> bool:
    """
    KeyBERT가 뽑은 키워드 중 자소서/기업분석에 부적절한 표현 제거.
    """
    if not keyword:
        return False

    keyword = keyword.strip()

    # 너무 짧거나 긴 문장 제거
    if len(keyword) < 2 or len(keyword) > 25:
        return False

    # 숫자/표/임원 데이터성 키워드 제거
    if re.search(r"\d", keyword):
        return False

    banned_tokens = [
        "당사는",
        "다음과",
        "요약현황",
        "상근",
        "리더",
        "조직도",
        "연구개발비",
        "연결기준",
        "산정되었습니다",
        "학교",
        "국가고시",
        "브라우저",
        "서울대",
        "kaist",
        "전산학",
        "학과",
        "박사",
        "석사",
        "보유",
        "주식",
        "기준일",
        "성명",
        "생년월",
    ]

    if any(token.lower() in keyword.lower() for token in banned_tokens):
        return False

    return True

def normalize_keyword(keyword: str) -> str | None:
    """
    KeyBERT가 뽑은 문장형 키워드를 Resume Agent용 대표 키워드로 정규화.
    KeyBERT 추출 결과를 버리는 게 아니라, 기업 분석에 쓰기 좋은 형태로 변환.
    """
    if not keyword:
        return None

    k = keyword.lower().strip()

    keyword_map = [
        (["생성형", "hyperclova", "ai서비스", "ai 서비스", "인공지능", "ai"], "생성형 AI"),
        (["검색", "서치플랫폼", "정보탐색"], "검색 플랫폼"),
        (["커머스", "쇼핑", "판매", "중개"], "커머스"),
        (["핀테크", "페이", "금융"], "핀테크"),
        (["웹툰", "콘텐츠", "스노우", "넷플릭스", "ip"], "콘텐츠/IP"),
        (["클라우드", "naver cloud", "iaas", "paas", "saas", "엔터프라이즈"], "클라우드/엔터프라이즈"),
        (["b2b", "기업용", "협업 솔루션", "라인웍스", "works"], "B2B 플랫폼"),
        (["글로벌", "일본", "북미", "사우디"], "글로벌 확장"),
        (["인프라", "idc", "트래픽", "플랫폼 기술"], "인프라/서비스 운영"),
        (["데이터", "내부 데이터를", "분석"], "데이터 활용"),
        (["자동화", "효율성", "비즈니스 효율"], "업무 자동화"),
        (["기술플랫폼", "기술 플랫폼", "연구개발", "기술을 고도화"], "기술 플랫폼/R&D"),
        (["사용자 경험", "사용자", "이용자"], "사용자 경험"),
    ]

    for triggers, normalized in keyword_map:
        if any(trigger in k for trigger in triggers):
            return normalized

    # 의미 없는 공시/표현 제거
    banned = [
        "벤처기업",
        "주주가치",
        "건강한 조직문화",
        "요약현황",
        "다음과 같습니다",
        "리더",
        "상근",
        "학력",
        "주식",
    ]

    if any(b in k for b in banned):
        return None

    # 너무 문장형이면 버림
    if len(keyword) > 18:
        return None

    return keyword.strip()


def extract_keywords_by_keybert(text: str, top_k: int = 15):
    """
    Step 4. KeyBERT로 회사 핵심 키워드 자동 추출.
    KeyBERT 원본 추출 → 노이즈 제거 → 대표 키워드 정규화 → 중복 제거.
    """
    if not text or not text.strip():
        return []
    
    cleaned_text = preprocess_text_for_keybert(text)
    # 너무 긴 텍스트를 그대로 넣으면 느려질 수 있으므로 일부만 사용.
    text_for_keyword = cleaned_text[:15000]

    raw_keywords = keyword_model.extract_keywords(
        text_for_keyword,
        keyphrase_ngram_range=(1, 3),
        stop_words=[
            "당사는", "또한", "그리고", "있습니다", "합니다", "대한", "위한",
            "통해", "관련", "기준", "다음", "상기", "경우", "현재",
            "주요", "서비스", "사업", "부문", "내용"
        ],
        top_n=top_k * 5,
        use_mmr=True,
        diversity=0.7
    )

    keywords = []
    seen = set()

    for keyword, score in raw_keywords:
        raw_keyword = str(keyword).strip()

        if not is_valid_keyword(raw_keyword):
            continue
        normalized = normalize_keyword(raw_keyword)

        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)

        keywords.append({
            "keyword": normalized,
            "raw_keyword": raw_keyword,
            "score": round(float(score), 4)
        })

        if len(keywords) >= top_k:
            break

    return keywords

def match_user_skills_to_keywords(user_skills: list, company_keywords: list, threshold: float = 0.6):
    """
    Step 5. 사용자 skills와 회사 키워드 간 cosine similarity 계산.
    """
    matching_points = []
    matched_keywords = set()

    for skill in user_skills:
        skill_embedding = embedding_model.encode(skill)

        for keyword_item in company_keywords:
            keyword = keyword_item["keyword"]
            keyword_embedding = embedding_model.encode(keyword)

            score = calculate_cosine_similarity(skill_embedding, keyword_embedding)

            if score >= threshold:
                matching_points.append({
                    "user_skill": skill,
                    "company_keyword": keyword,
                    "fit_score": round(score, 2)
                })
                matched_keywords.add(keyword)

    return matching_points, matched_keywords


def derive_evidence_gaps(company_keywords: list, matched_keywords: set):
    """
    Step 6. 매칭 안 된 회사 키워드 = 사용자가 자소서에서 보강해야 할 부분.
    """
    all_keywords = [item["keyword"] for item in company_keywords]
    gaps = [keyword for keyword in all_keywords if keyword not in matched_keywords]

    return gaps


def map_story_angles(company_keywords: list, matched_keywords: set):
    """
    Step 7. 키워드 패턴 → 사전 정의 Story Angle 매핑.
    """
    keyword_text = " ".join([item["keyword"] for item in company_keywords])
    matched_text = " ".join(list(matched_keywords))
    combined_text = keyword_text + " " + matched_text

    story_angles = []

    if any(token in combined_text for token in ["AI", "인공지능", "생성형", "LLM", "RAG", "HyperCLOVA", "연구개발"]):
        story_angles.append("기술적 깊이: AI/R&D 기반 문제 해결 경험을 기업의 기술 전략과 연결")

    if any(token in combined_text for token in ["검색", "추천", "광고", "커머스", "고객", "사용자"]):
        story_angles.append("사용자 경험 개선: 데이터와 검색/추천 기술로 사용자 문제를 해결한 경험 강조")

    if any(token in combined_text for token in ["트래픽", "클라우드", "인프라", "서비스", "운영", "IDC"]):
        story_angles.append("서비스 확장성: 안정적인 운영, 트래픽 처리, 인프라 관점의 실행력 어필")

    if any(token in combined_text for token in ["글로벌", "콘텐츠", "웹툰", "B2B", "엔터프라이즈"]):
        story_angles.append("사업 확장성: 글로벌·B2B·콘텐츠 확장 방향과 본인 경험 연결")

    if any(token in combined_text for token in ["자동화", "문서", "Vision", "멀티모달", "이미지"]):
        story_angles.append("업무 자동화: AI를 활용해 반복 업무를 줄이고 실무 효율을 높인 경험 강조")

    if not story_angles:
        story_angles.append("기업 사업 방향과 본인의 프로젝트 경험을 연결한 문제 해결형 스토리 구성")

    return story_angles


async def run_resume_agent(profile: dict, collection) -> dict:
    """
    Resume Agent 역할:
    1. target_company가 ChromaDB에 인덱싱되어 있는지 확인
    2. companies 컬렉션에서 DART 청크 검색
    3. 청크 합치기
    4. KeyBERT로 회사 핵심 키워드 추출
    5. 사용자 skills와 회사 키워드 cosine similarity 매칭
    6. gaps 도출
    7. Story Angle 룰 매핑
    8. 네이버 뉴스 Dynamic RAG 추가
    """
    target_company = profile["target_company"]
    user_skills = profile.get("skills", [])
    target_role = profile.get("target_role", "")

    if target_role:
        user_skills = user_skills + [target_role]

    print(f"\n🚀 {target_company} Resume Agent 작동 시작")

    # Step 1. 사전 인덱싱 체크
    if not check_company_indexed(collection, target_company):
        return {
            "agent_name": "resume",
            "items": [],
            "sources": ["ChromaDB companies"],
            "metadata": {
                "llm_used": False,
                "target_company": target_company
            },
            "error": f"{target_company}는 인덱싱되지 않은 기업입니다."
        }

    company_metadata = get_company_metadata(collection, target_company)
    company_identifier = company_metadata.get("company_identifier") if company_metadata else None

    print(f"✅ 기업 정보 확인 완료: {target_company} / {company_identifier}")

    # Step 2. ChromaDB 검색
    print("🔍 DART 공시 검색 중")
    retrieved_chunks, metadatas = retrieve_company_chunks(
        collection=collection,
        company_name=target_company,
        k=15
    )

    if not retrieved_chunks:
        return {
            "agent_name": "resume",
            "items": [],
            "sources": ["ChromaDB companies"],
            "metadata": {
                "llm_used": False,
                "target_company": target_company,
                "company_identifier": company_identifier
            },
            "error": f"{target_company}의 공시 청크 검색 결과가 없습니다."
        }

    # Step 3. 청크 합치기
    merged_disclosure_text = "\n".join(retrieved_chunks)

    # Step 4. KeyBERT 키워드 추출
    print("🔑 기업 핵심 키워드 추출 중")
    company_keywords = extract_keywords_by_keybert(
        text=merged_disclosure_text,
        top_k=15
    )

    # Step 5. 사용자 skills와 cosine similarity 매칭
    print("🧮 사용자 역량과 기업 키워드 매칭 중")
    matching_points, matched_keywords = match_user_skills_to_keywords(
        user_skills=user_skills,
        company_keywords=company_keywords,
        threshold=0.6
    )

    # Step 6. gaps 도출
    evidence_gaps = derive_evidence_gaps(
        company_keywords=company_keywords,
        matched_keywords=matched_keywords
    )

    # Step 7. Story Angle 룰 매핑
    story_angles = map_story_angles(
        company_keywords=company_keywords,
        matched_keywords=matched_keywords
    )

    # Step 8. Dynamic RAG: 네이버 뉴스
    print("🌐 네이버 뉴스 트렌드 수집 중")
    dynamic_news = await fetch_naver_news(target_company)

    return {
        "agent_name": "resume",
        "company": target_company,
        "company_identifier": company_identifier,
        "emphasize_keywords": company_keywords,
        "matching_points": matching_points,
        "evidence_gaps": evidence_gaps,
        "story_angles": story_angles,
        "dynamic_news": dynamic_news,
        "static_disclosure_chunks": retrieved_chunks[:5],
        "retrieved_chunk_count": len(retrieved_chunks),
        "sources": ["ChromaDB companies", "DART disclosure chunks", "Naver News API"],
        "metadata": {
            "llm_used": False,
            "retrieval_k": len(retrieved_chunks)
        },
        "error": None
    }


# ============================================================
# 7. Formatter + Context Saver
# ============================================================
def format_agent_output_to_text(data: dict) -> str:
    if data.get("error"):
        return f"[자소서 결과]\n{data['error']}"

    formatted_disclosures = "\n".join([
        f"- {chunk[:400]}..."
        for chunk in data.get("static_disclosure_chunks", [])
    ])

    formatted_news = "\n".join([
        f"- {news['title']} ({news['link']})"
        for news in data.get("dynamic_news", [])
    ])

    keyword_text = ", ".join([
        f"{item['keyword']}({item['score']})"
        for item in data.get("emphasize_keywords", [])
    ])

    formatted_matching = "\n".join([
        f"- 내 역량 [{m['user_skill']}] ↔ 기업 키워드 [{m['company_keyword']}] "
        f"(매칭 적합도: {int(m['fit_score'] * 100)}%)"
        for m in data.get("matching_points", [])
    ])

    formatted_gaps = ", ".join(data.get("evidence_gaps", [])) if data.get("evidence_gaps") else "없음"

    formatted_angles = "\n".join([
        f"- {angle}"
        for angle in data.get("story_angles", [])
    ])

    text_context = f"""
[분석 대상 기업]
{data['company']} ({data.get('company_identifier')})

[Static RAG: DART 공시 기반 기업 사업 방향 근거]
{formatted_disclosures if formatted_disclosures else "- 공시 기반 검색 결과 부족"}

[Dynamic RAG: 네이버 뉴스 기반 최신 트렌드]
{formatted_news if formatted_news else "- 최신 뉴스 검색 결과 부족"}

[KeyBERT 기반 기업 핵심 키워드]
{keyword_text if keyword_text else "- 키워드 추출 결과 부족"}

[사용자 정보와 기업 컨텍스트 매칭 결과]
{formatted_matching if formatted_matching else "- 현재 사용자 역량과 직접 매칭되는 포인트가 부족합니다."}

[자소서에서 보강하면 좋은 기업 이해 포인트]
{formatted_gaps}

[추천 자기소개서 Story Angle]
{formatted_angles if formatted_angles else "- 추천 Story Angle 부족"}
"""
    return text_context


def save_resume_agent_context(agent_output: dict, context_text: str, output_dir: str = "agent_outputs") -> str:
    os.makedirs(output_dir, exist_ok=True)

    company = agent_output.get("company", "company")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"resume_context_{company}_{timestamp}.json")

    payload = {
        "agent_name": "resume",
        "items": [
            {
                "company": agent_output.get("company"),
                "company_identifier": agent_output.get("company_identifier"),
                "emphasize_keywords": agent_output.get("emphasize_keywords", []),
                "matching_points": agent_output.get("matching_points", []),
                "evidence_gaps": agent_output.get("evidence_gaps", []),
                "story_angles": agent_output.get("story_angles", []),
                "dynamic_news": agent_output.get("dynamic_news", []),
                "static_disclosure_chunks": agent_output.get("static_disclosure_chunks", []),
                "retrieved_chunk_count": agent_output.get("retrieved_chunk_count", 0)
            }
        ],
        "context_text": context_text,
        "sources": agent_output.get("sources", []),
        "metadata": {
            **agent_output.get("metadata", {}),
            "created_at": timestamp,
            "note": "Final answer generation is delegated to the integrated LLM/router."
        },
        "error": agent_output.get("error")
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return output_path


# ============================================================
# 8. Main
# ============================================================
async def main():
    """
    테스트용 실행부.
    Streamlit/FastAPI 통합 후에는 test_profile 부분만 외부 입력으로 대체.
    """

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

    target_company = test_profile["target_company"]
    company_identifier = test_profile["company_identifier"]
    base_date = "2025-01-01"

    vector_builder = DartDisclosureVectorBuilder()
    collection = vector_builder.collection

    # 테스트 편의용:
    # ChromaDB에 기업이 없으면 DART로 1회 인덱싱.
    # 이미 있으면 DART 재호출 없이 ChromaDB만 사용.
    if check_company_indexed(collection, target_company):
        print(f"✅ 기존 {target_company} DART 공시 정보가 있어 재수집을 생략합니다.")
    else:
        print(f"⚠️ {target_company}에 대한 DART 공시 정보가 없어 새로 수집합니다.")
        collection = vector_builder.build_vector_db(
            company_identifier=company_identifier,
            company_name=target_company,
            start_date=base_date
        )

    agent_output = await run_resume_agent(
        profile=test_profile,
        collection=collection
    )

    context_text = format_agent_output_to_text(agent_output)

    saved_context_path = save_resume_agent_context(
        agent_output=agent_output,
        context_text=context_text
    )

    print("\n✅ Resume Agent Context 저장 완료")
    print(f"저장 위치: {saved_context_path}")
    print("\n📝 [저장된 Context 미리보기]")
    print(context_text)


if __name__ == "__main__":
    asyncio.run(main())

