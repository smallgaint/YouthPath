import streamlit as st
import requests
import pandas as pd
import calendar
import difflib
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

st.set_page_config(
    page_title="YouthPath",
    layout="wide"
)

# =========================
# session state
# =========================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "response_data" not in st.session_state:
    st.session_state.response_data = None

if "saved_events" not in st.session_state:
    st.session_state.saved_events = []

if "selected_skills" not in st.session_state:
    st.session_state.selected_skills = ["Python"]

if "selected_roles" not in st.session_state:
    st.session_state.selected_roles = ["데이터 분석가"]

ADMIN_REGION_XLSX_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "전국 시군구 행정구역 목록.xlsx",
    Path(__file__).resolve().parent / "전국 시군구 행정구역 목록.xlsx",
    Path.home() / "OneDrive" / "바탕 화면" / "전국 시군구 행정구역 목록.xlsx",
    Path.home() / "Desktop" / "전국 시군구 행정구역 목록.xlsx",
]

SKILL_XLSX_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "보유 기술.xlsx",
    Path(__file__).resolve().parent / "보유 기술.xlsx",
    Path.home() / "OneDrive" / "바탕 화면" / "보유 기술.xlsx",
    Path.home() / "Desktop" / "보유 기술.xlsx",
]

ROLE_XLSX_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "희망직무.xlsx",
    Path(__file__).resolve().parent / "희망직무.xlsx",
    Path.home() / "OneDrive" / "바탕 화면" / "희망직무.xlsx",
    Path.home() / "Desktop" / "희망직무.xlsx",
]

SIDO_SHORT_NAMES = {
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "경기도": "경기",
    "강원특별자치도": "강원",
    "강원도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전북특별자치도": "전북",
    "전라북도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
    "제주특별자치도": "제주",
}

def normalize_region_text(value):
    return re.sub(r"[\s,·/()]+", "", str(value or "")).lower()

@st.cache_data(show_spinner=False)
def load_admin_regions():
    xlsx_path = next((path for path in ADMIN_REGION_XLSX_CANDIDATES if path.exists()), None)
    if not xlsx_path:
        return []

    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(xlsx_path) as archive:
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        shared_strings = []
        for item in shared_root.findall("a:si", ns):
            shared_strings.append("".join(text.text or "" for text in item.findall(".//a:t", ns)))

        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        regions = []
        seen = set()

        for row in sheet.findall(".//a:row", ns):
            values = []
            for cell in row.findall("a:c", ns):
                value_node = cell.find("a:v", ns)
                value = "" if value_node is None else value_node.text or ""
                if cell.get("t") == "s" and value:
                    value = shared_strings[int(value)]
                values.append(value.strip())

            if len(values) < 4 or values[0] in ("", "대분류", "전국행정동리스트"):
                continue

            sido, sigun, gu, dong = (values + ["", "", "", ""])[:4]
            parts = [part for part in [sido, sigun, gu, dong] if part]
            full_name = " ".join(parts)
            key = normalize_region_text(full_name)
            if not full_name or key in seen:
                continue
            seen.add(key)
            regions.append({
                "sido": sido,
                "sido_short": SIDO_SHORT_NAMES.get(sido, sido),
                "sigun": sigun,
                "gu": gu,
                "dong": dong,
                "full_name": full_name,
                "search_key": key,
            })

    return regions

def find_admin_region(user_input):
    regions = load_admin_regions()
    query = normalize_region_text(user_input)
    if not query or not regions:
        return None

    for region_item in regions:
        if query == region_item["search_key"] or query in region_item["search_key"]:
            return region_item

    choices = {region_item["search_key"]: region_item for region_item in regions}
    match = difflib.get_close_matches(query, choices.keys(), n=1, cutoff=0.55)
    return choices[match[0]] if match else None

def normalize_skill_text(value):
    return re.sub(r"[\s,·/_()+#.-]+", "", str(value or "")).lower()

@st.cache_data(show_spinner=False)
def load_skill_keywords():
    xlsx_path = next((path for path in SKILL_XLSX_CANDIDATES if path.exists()), None)
    if not xlsx_path:
        return ["Python", "SQL", "React", "Java", "Excel"]

    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(xlsx_path) as archive:
        shared_strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("a:si", ns):
                shared_strings.append("".join(text.text or "" for text in item.findall(".//a:t", ns)))

        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        skills = []
        seen = set()

        for row in sheet.findall(".//a:row", ns):
            for cell in row.findall("a:c", ns):
                value_node = cell.find("a:v", ns)
                value = "" if value_node is None else value_node.text or ""
                if cell.get("t") == "s" and value:
                    value = shared_strings[int(value)]
                value = value.strip()
                if not value or value in ("보유기술/자격증/툴 키워드", "보유 기술"):
                    continue
                key = normalize_skill_text(value)
                if key and key not in seen:
                    seen.add(key)
                    skills.append(value)

    return skills

def find_skill_suggestions(user_input, limit=8):
    skills = load_skill_keywords()
    query = normalize_skill_text(user_input)
    if not query:
        return []

    contains = [
        skill for skill in skills
        if query in normalize_skill_text(skill)
    ]
    if contains:
        return contains[:limit]

    choices = {normalize_skill_text(skill): skill for skill in skills}
    matches = difflib.get_close_matches(query, choices.keys(), n=limit, cutoff=0.45)
    return [choices[match] for match in matches]

@st.cache_data(show_spinner=False)
def load_role_keywords():
    xlsx_path = next((path for path in ROLE_XLSX_CANDIDATES if path.exists()), None)
    if not xlsx_path:
        return ["데이터 분석가", "백엔드 개발자", "프론트엔드 개발자", "기획", "마케팅"]

    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(xlsx_path) as archive:
        shared_strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("a:si", ns):
                shared_strings.append("".join(text.text or "" for text in item.findall(".//a:t", ns)))

        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        roles = []
        seen = set()

        for row in sheet.findall(".//a:row", ns):
            for cell in row.findall("a:c", ns):
                value_node = cell.find("a:v", ns)
                value = "" if value_node is None else value_node.text or ""
                if cell.get("t") == "s" and value:
                    value = shared_strings[int(value)]
                value = value.strip()
                if not value or value in ("희망 직무", "희망직무"):
                    continue
                key = normalize_skill_text(value)
                if key and key not in seen:
                    seen.add(key)
                    roles.append(value)

    return roles

def find_role_suggestions(user_input, limit=8):
    roles = load_role_keywords()
    query = normalize_skill_text(user_input)
    if not query:
        return []

    contains = [
        role for role in roles
        if query in normalize_skill_text(role)
    ]
    if contains:
        return contains[:limit]

    choices = {normalize_skill_text(role): role for role in roles}
    matches = difflib.get_close_matches(query, choices.keys(), n=limit, cutoff=0.45)
    return [choices[match] for match in matches]

def parse_experience_text(text):
    text = str(text or "").strip().lower()
    if not text:
        return {"years": 0, "months": 0, "label": "신입"}

    if any(token in text for token in ["신입", "없음", "무경력", "경력없", "0년", "0개월"]):
        return {"years": 0, "months": 0, "label": "신입"}

    years = 0
    months = 0

    year_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:년|year|years|yr)", text)
    month_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:개월|달|month|months|mo)", text)

    if year_match:
        years = float(year_match.group(1))
    if month_match:
        months = int(round(float(month_match.group(1))))

    if not year_match and not month_match:
        number_match = re.search(r"\d+(?:\.\d+)?", text)
        if number_match:
            years = float(number_match.group(0))

    total_months = int(round(years * 12)) + months
    normalized_years = total_months // 12
    remaining_months = total_months % 12

    if total_months == 0:
        label = "신입"
    elif normalized_years and remaining_months:
        label = f"{normalized_years}년 {remaining_months}개월"
    elif normalized_years:
        label = f"{normalized_years}년"
    else:
        label = f"{remaining_months}개월"

    return {
        "years": normalized_years,
        "months": total_months,
        "label": label,
    }

def add_event_to_calendar(event):
    try:
        event_date = datetime.strptime(event["date"], "%Y-%m-%d")
    except (KeyError, TypeError, ValueError):
        st.warning("마감일이 있는 항목만 캘린더에 추가할 수 있습니다.")
        return

    exists = any(
        saved_event["title"] == event["title"]
        and saved_event["date"] == event["date"]
        for saved_event in st.session_state.saved_events
    )

    if not exists:
        st.session_state.saved_events.append(event)

    st.session_state.calendar_year = event_date.year
    st.session_state.calendar_month = event_date.month
    st.session_state.selected_day = event_date.day
    st.session_state.page = "mypage"
    st.rerun()

def delete_event_from_calendar(event):
    st.session_state.saved_events = [
        saved_event
        for saved_event in st.session_state.saved_events
        if not (
            saved_event["title"] == event["title"]
            and saved_event["date"] == event["date"]
            and saved_event["source"] == event["source"]
        )
    ]

    st.rerun()

def get_event_color(event):
    if event.get("source") == "policy":
        return "#c92a2a"
    if event.get("source") == "job":
        return "#4263eb"
    return "#ae3ec9"

def render_calendar_event_bar(event):
    title = event.get("title", "일정")
    color = get_event_color(event)
    return f"""
    <div style="
        margin-top: 4px;
        padding: 3px 6px;
        border-radius: 4px;
        background: {color};
        color: white;
        font-size: 12px;
        font-weight: 700;
        line-height: 1.25;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;">
        {title}
    </div>
    """

def normalize_link(link):
    link = (link or "").strip()
    if not link:
        return "https://www.youthcenter.go.kr"
    if link.startswith(("http://", "https://")):
        return link
    return f"https://{link}"

# =========================
# Sidebar
# =========================

with st.sidebar:

    st.title("🎓 YouthPath")
    st.caption("청년 사회진입 통합 AI 서비스")

    st.divider()

    st.subheader("👤 프로필")

    age = st.selectbox(
        "나이",
        list(range(19, 40)),
        index=8
    )

    region_input = st.text_input(
        "거주지",
        value="서울",
        placeholder="예: 서울 강남구 역삼동"
    )

    matched_region = find_admin_region(region_input)
    if matched_region:
        region = matched_region["sido_short"]
        region_full = matched_region["full_name"]
        st.caption(f"인식된 거주지: {region_full}")
    else:
        region = region_input.strip() or "서울"
        region_full = region
        st.caption("행정구역 목록에서 정확히 찾지 못해 입력값을 그대로 사용합니다.")

    income = st.selectbox(
        "소득 구간",
        [
            "중위 60% 이하",
            "중위 80% 이하",
            "중위 100% 이하"
        ]
    )

    education = st.selectbox(
        "학력",
        [
            "고등학교 졸업",
            "전문대 졸업",
            "4년제 졸업",
            "대학원"
        ]
    )

    st.markdown("보유 기술")
    skill_query = st.text_input(
        "보유 기술 검색",
        placeholder="예: 파이썬, SQL, 정보처리기사",
        label_visibility="collapsed",
        key="skill_query"
    )
    skill_suggestions = find_skill_suggestions(skill_query)

    if skill_suggestions:
        selected_skill_candidate = st.selectbox(
            "연관검색어",
            skill_suggestions,
            label_visibility="collapsed",
            key="skill_candidate"
        )
        if st.button("기술 추가", key="add_skill_button"):
            if selected_skill_candidate not in st.session_state.selected_skills:
                st.session_state.selected_skills.append(selected_skill_candidate)
            st.rerun()
    elif skill_query:
        st.caption("연관 기술을 찾지 못했습니다.")

    if st.session_state.selected_skills:
        st.markdown("선택된 보유 기술")
        for idx, selected_skill in enumerate(list(st.session_state.selected_skills)):
            col_skill, col_remove = st.columns([4, 1])
            with col_skill:
                st.markdown(
                    f"""
                    <div style="
                        display: inline-block;
                        margin-bottom: 6px;
                        padding: 6px 10px;
                        border-radius: 8px;
                        background: #ffe3e3;
                        color: #c92a2a;
                        font-weight: 700;">
                        {selected_skill}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_remove:
                if st.button("×", key=f"remove_skill_{idx}_{selected_skill}"):
                    st.session_state.selected_skills.remove(selected_skill)
                    st.rerun()

    skills = st.session_state.selected_skills

    experience_input = st.text_input(
        "경력",
        value="신입",
        placeholder="예: 신입, 6개월, 1년 3개월, 2년"
    )
    parsed_experience = parse_experience_text(experience_input)
    experience = parsed_experience["years"]
    experience_months = parsed_experience["months"]
    st.caption(f"인식된 경력: {parsed_experience['label']}")

    st.markdown("희망 직무")
    role_query = st.text_input(
        "희망 직무 검색",
        placeholder="예: 데이터 분석가, 백엔드 개발자",
        label_visibility="collapsed",
        key="role_query"
    )
    role_suggestions = find_role_suggestions(role_query)

    if role_suggestions:
        selected_role_candidate = st.selectbox(
            "직무 연관검색어",
            role_suggestions,
            label_visibility="collapsed",
            key="role_candidate"
        )
        if st.button("직무 추가", key="add_role_button"):
            if selected_role_candidate not in st.session_state.selected_roles:
                st.session_state.selected_roles.append(selected_role_candidate)
            st.rerun()
    elif role_query:
        st.caption("연관 직무를 찾지 못했습니다.")

    if st.session_state.selected_roles:
        st.markdown("선택된 희망 직무")
        for idx, selected_role in enumerate(list(st.session_state.selected_roles)):
            col_role, col_remove = st.columns([4, 1])
            with col_role:
                st.markdown(
                    f"""
                    <div style="
                        display: inline-block;
                        margin-bottom: 6px;
                        padding: 6px 10px;
                        border-radius: 8px;
                        background: #e7f5ff;
                        color: #1864ab;
                        font-weight: 700;">
                        {selected_role}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_remove:
                if st.button("×", key=f"remove_role_{idx}_{selected_role}"):
                    st.session_state.selected_roles.remove(selected_role)
                    st.rerun()

    target_roles = st.session_state.selected_roles
    target_role = target_roles[0] if target_roles else ""

    target_company = st.selectbox(
        "관심 기업",
        [
            "네이버",
            "카카오",
            "삼성전자",
            "LG전자",
            "SK하이닉스",
            "현대자동차",
            "기아",
            "쿠팡",
            "토스",
            "라인",
            "배달의민족",
            "선택 안 함"
        ]
    )
    target_company = "" if target_company == "선택 안 함" else target_company

    st.divider()

    if st.button("📅 마이페이지"):
        st.session_state.page = "mypage"

    if st.button("🏠 홈"):
        st.session_state.page = "home"

# =========================
# HOME PAGE
# =========================

if st.session_state.page == "home":

    st.title("YouthPath")

    query = st.text_input(
        "궁금한 점을 자연어로 물어보세요",
        placeholder="서울에서 월세 도와주는 정책이랑 IT 신입 공고 알려줘"
    )

    if st.button("🔍 질문하기"):

        response = requests.post(
            "http://127.0.0.1:8000/ask",
            json={
                "query": query,
                "profile": {
                    "age": age,
                    "region": region,
                    "region_full": region_full,
                    "income": income,
                    "education": education,
                    "skills": skills,
                    "experience": experience,
                    "experience_months": experience_months,
                    "experience_text": experience_input,
                    "experience_label": parsed_experience["label"],
                    "target_role": target_role,
                    "target_roles": target_roles,
                    "target_company": target_company
                }
            }
        )

        st.session_state.response_data = response.json()
        st.session_state.page = "output"
        st.rerun()

    st.markdown("### 💡 예시 질문")

    st.markdown("""
    - 청년 주거 지원 정책 뭐가 있어?
    - 데이터 분석가 신입 공고 추천해줘
    - 네이버 자소서 어떻게 써야 할까?
    - 이번 달 신청 마감 임박한 거 정리해줘
    - 서울에서 월세 도와주는 정책이랑 IT 신입 공고 알려줘
    """)

    st.info("""
    📘 사용 방법

    사이드바에서 프로필을 입력한 뒤 검색창에 자연어로 질문하세요.

    LangGraph Router가 의도를 분석해 적절한 Agent를 호출합니다.
    """)

    # =========================
    # Output
    # =========================

elif st.session_state.page == "output":
    if st.session_state.response_data:
        data = st.session_state.response_data
        st.title("📤 결과")
        st.success("Router가 Policy + Job Agent를 선택했습니다.")
        st.subheader("💬 답변")
        st.write(data["answer"])

        # =========================
        # 정책 결과
        # =========================

        st.subheader("📋 정책 결과")

        policy_data = data.get("policy", [])
        policy_items = policy_data.get("items", []) if isinstance(policy_data, dict) else policy_data

        for item in policy_items:

            with st.container(border=True):

                title = item.get("title", "정책")
                deadline = item.get("deadline") or item.get("date") or "미정"
                link = item.get("link") or item.get("url") or "https://www.youthcenter.go.kr"

                st.markdown(f"### {title}")
                st.caption(f"마감: {deadline}")

                st.write(
                    item.get("description")
                    or item.get("summary")
                    or item.get("benefit")
                    or "정책 설명이 제공되지 않았습니다."
                )

                matched_criteria = item.get("matched_criteria", [])
                if matched_criteria:
                    matched_text = ", ".join(
                        f"{criterion.get('label', '조건')} {criterion.get('user_value', '')}".strip()
                        for criterion in matched_criteria
                    )
                else:
                    matched_text = item.get("match", "조건 확인 필요")

                st.success(f"조건 일치: {matched_text}")

                col1, col2 = st.columns(2)

                with col1:
                    st.link_button(
                        "해당 사이트 가기",
                        link
                    )

                with col2:
                    if st.button(
                        "📅 캘린더 추가하기",
                        key=f"policy_calendar_{title}"
                    ):
                        add_event_to_calendar({
                            "title": title,
                            "date": deadline,
                            "type": "정책",
                            "source": "policy",
                            "link": link
                        })

        # =========================
        # 채용 결과
        # =========================

        st.subheader("💼 채용 결과")

        job_data = data.get("job", [])
        job_items = job_data.get("items", []) if isinstance(job_data, dict) else job_data

        for item in job_items:

            with st.container(border=True):

                company = item.get("company", "회사")
                title = item.get("title", "채용공고")
                deadline = item.get("deadline") or item.get("date") or "미정"
                link = item.get("url") or item.get("link") or "https://www.work.go.kr"

                st.markdown(f"### {company}")
                st.write(title)

                if item.get("days_remaining") is not None:
                    st.warning(f"D-{item['days_remaining']}")
                else:
                    st.warning(deadline)

                col1, col2 = st.columns(2)

                with col1:
                    st.link_button(
                        "해당 사이트 가기",
                        link
                        )

                with col2:
                    if st.button(
                        "📅 캘린더 추가하기",
                        key=f"job_calendar_{company}_{title}"
                    ):
                        add_event_to_calendar({
                            "title": f"{company} {title}",
                            "date": deadline,
                            "type": "채용",
                            "source": "job",
                            "link": link
                        })
        if st.button("🏠 홈으로 돌아가기"):
            st.session_state.page = "home"
            st.rerun()

    else:
        st.warning("아직 결과가 없습니다. 먼저 질문을 입력해주세요.")
        if st.button("홈으로 이동"):
            st.session_state.page = "home"
            st.rerun()
# =========================
# MY PAGE
# =========================

elif st.session_state.page == "mypage":

    st.title("🗓️ 마이페이지")

    # =========================
    # 현재 월 상태 관리
    # =========================
    today = datetime.today()

    if "calendar_year" not in st.session_state:
        st.session_state.calendar_year = today.year

    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = today.month

    year = st.session_state.calendar_year
    month = st.session_state.calendar_month

    # =========================
    # 더미 이벤트 데이터
    # 나중에는 DynamoDB에서 가져오면 됨
    # =========================
    events = []
    for saved_event in st.session_state.saved_events:
        event_date = datetime.strptime(saved_event["date"], "%Y-%m-%d")

        if event_date.year == year and event_date.month == month:
            d_day_num = (event_date.date() - today.date()).days

            if d_day_num >= 0:
                d_day = f"D-{d_day_num}"
            else:
                d_day = f"D+{abs(d_day_num)}"

            events.append({
                **saved_event,
                "day": event_date.day,
                "d_day": d_day
            })

    # 날짜별 이벤트 묶기
    events_by_day = {}
    for event in events:
        events_by_day.setdefault(event["day"], []).append(event)

    # 선택 날짜 기본값
    if "selected_day" not in st.session_state:
        st.session_state.selected_day = today.day

    # =========================
    # 달력 상단
    # =========================
    col_title, col_nav = st.columns([5, 1])

    with col_title:
        st.subheader("🗓️ 내 일정 달력")

    with col_nav:
        nav1, nav2, nav3 = st.columns(3)

        with nav1:
            if st.button("◀"):
                if month == 1:
                    st.session_state.calendar_year -= 1
                    st.session_state.calendar_month = 12
                else:
                    st.session_state.calendar_month -= 1
                st.rerun()

        with nav2:
            st.markdown(f"**{year}. {month:02d}**")

        with nav3:
            if st.button("▶"):
                if month == 12:
                    st.session_state.calendar_year += 1
                    st.session_state.calendar_month = 1
                else:
                    st.session_state.calendar_month += 1
                st.rerun()

    # =========================
    # 전체 레이아웃: 왼쪽 달력 / 오른쪽 패널
    # =========================
    left, right = st.columns([3, 1.35])

    # =========================
    # 왼쪽: 달력
    # =========================
    with left:

        st.markdown(
            """
            <style>
            div[data-testid="stVerticalBlock"] div[data-testid="stButton"] button {
                min-height: 38px;
            }
            div[data-testid="stVerticalBlock"] div[data-testid="stButton"] {
                margin-bottom: -8px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        weekdays = ["일", "월", "화", "수", "목", "금", "토"]

        # calendar.monthcalendar는 월요일 시작이라, 일요일 시작으로 바꿔줌
        calendar.setfirstweekday(calendar.SUNDAY)
        month_calendar = calendar.monthcalendar(year, month)

        header_cols = st.columns(7)
        for i, day_name in enumerate(weekdays):
            if day_name == "일":
                header_cols[i].markdown(f"<span style='color:#ff4b4b; font-weight:700'>{day_name}</span>", unsafe_allow_html=True)
            elif day_name == "토":
                header_cols[i].markdown(f"<span style='color:#1f77ff; font-weight:700'>{day_name}</span>", unsafe_allow_html=True)
            else:
                header_cols[i].markdown(f"**{day_name}**")

        for week in month_calendar:
            week_cols = st.columns(7)

            for i, day in enumerate(week):
                with week_cols[i]:

                    if day == 0:
                        st.markdown(
                            """
                            <div style="
                                min-height: 118px;
                                border: 1px solid #eeeeee;
                                border-radius: 4px;
                                background-color: #fafafa;">
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    else:
                        is_selected = day == st.session_state.selected_day
                        has_events = day in events_by_day

                        # 날짜 선택 버튼
                        if st.button(str(day), key=f"day_{day}"):
                            st.session_state.selected_day = day
                            st.rerun()

                        # 이벤트 표시
                        cell_bg = "#eef4ff" if is_selected else "#ffffff"
                        cell_border = "#1c3f77" if is_selected else "#e5e7eb"
                        event_bars = ""

                        if has_events:
                            event_bars = "".join(
                                render_calendar_event_bar(event)
                                for event in events_by_day[day][:3]
                            )
                            if len(events_by_day[day]) > 3:
                                event_bars += f"""
                                <div style="
                                    margin-top: 4px;
                                    color: #868e96;
                                    font-size: 11px;">
                                    +{len(events_by_day[day]) - 3}개 더
                                </div>
                                """

                        st.markdown(
                            f"""
                            <div style="
                                min-height: 86px;
                                margin-top: -4px;
                                margin-bottom: 18px;
                                padding: 4px;
                                border: 2px solid {cell_border};
                                border-radius: 6px;
                                background: {cell_bg};">
                                {event_bars}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

        st.caption("🔴 정책 마감  |  🔵 채용 마감  |  🟣 직접 추가")

    # =========================
    # 오른쪽: 선택 날짜 패널
    # =========================
    with right:

        selected_day = st.session_state.selected_day
        selected_events = events_by_day.get(selected_day, [])

        with st.container(border=True):
            st.markdown("### ➕ 직접 일정 추가")

            custom_title = st.text_input(
                "일정 제목",
                placeholder="예: 포트폴리오 제출 마감"
            )

            custom_date = st.date_input(
                "일정 날짜",
                value=datetime(year, month, selected_day).date()
            )

            custom_link = st.text_input(
                "관련 링크",
                placeholder="https://..."
            )

            if st.button("직접 추가하기"):
                add_event_to_calendar({
                    "title": custom_title,
                    "date": custom_date.strftime("%Y-%m-%d"),
                    "type": "직접 추가",
                    "source": "manual",
                    "link": normalize_link(custom_link)
                })

        with st.container(border=True):
            st.markdown(f"### ▼ 그 날의 이벤트 ({len(selected_events)}건)")

            if selected_events:
                for event in selected_events:
                    st.markdown(f"**💼 {event['title']}**")
                    st.caption(f"마감: {event['date']} · {event['d_day']}")

                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.link_button("해당 사이트로 가기 →", normalize_link(event.get("link")))
                    with c2:
                        if st.button(
                            "삭제",
                            key=f"delete_{event['source']}_{event['title']}_{event['date']}"
                        ):
                            delete_event_from_calendar(event)

                    st.divider()
            else:
                st.caption("다른 날짜 클릭 시 해당 날의 이벤트로 교체됩니다.")

        with st.container(border=True):
            if events:
                st.info(
                    f"""
                    📘 이번 달 요약

                    총 {len(events)}건  
                    가장 임박: {events[0]['title']} ({events[0]['d_day']})  
                    가장 먼 일정: {events[-1]['title']} ({events[-1]['d_day']})
                    """
                )
            else:
                st.info(
                    """
                    📘 이번 달 요약

                    아직 추가된 일정이 없습니다.  
                    결과 화면에서 '캘린더 추가하기'를 눌러 일정을 모아보세요.
                    """
                )

    st.divider()

    if st.button("🏠 홈으로 돌아가기"):
        st.session_state.page = "home"
        st.rerun()
