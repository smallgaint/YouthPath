import streamlit as st
import requests
import pandas as pd
import calendar
import json
import base64
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# 로그인/본인인증을 요구하는 포털 경로 패턴 → 해당 시 로그인 없는 검색으로 우회
# (공개 링크는 그대로 직접 연결, 아래 패턴에 걸리는 것만 검색으로 대체)
_LOGIN_PRONE = (
    "ai-recruit", "moveTWAT", "rcvfvrSvc", "savingsAccount", "/ssis-tbu/", "login",
    "khug.or.kr",  # 주택도시보증공사 채용시스템 (로그인 요구)
)


def _job_link_safe(url: str, title: str):
    """채용 링크: 로그인 요구 포털이면 네이버 채용 검색으로 우회. 반환 (라벨, URL)."""
    url = (url or "").strip()
    title = (title or "").strip()
    if url and not any(p in url for p in _LOGIN_PRONE):
        return "🌐 사이트 바로가기", url
    if title:
        return "🔎 검색으로 보기", "https://search.naver.com/search.naver?query=" + quote(title + " 채용")
    return None, None
import streamlit.components.v1 as components
from html import escape
from frontend.components.mypage import render_mypage


st.set_page_config(
    page_title="YouthPath",
    page_icon="logo.png",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────
# 플랫폼 느낌 글로벌 스타일 (Linkareer 풍: 밝은 블루 + 화이트 카드 + D-day 뱃지)
# ──────────────────────────────────────────────────────────────────────
_YP_STYLE = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
:root {
--yp-brand: #1E6BFF; --yp-brand-dark: #1550CC; --yp-bg: #F4F6FB;
--yp-card: #FFFFFF; --yp-border: #E6E9F2; --yp-text: #1A1F36; --yp-muted: #6B7280;
}
html, body, [class*="css"], .stApp, button, input, textarea, select {
font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Segoe UI', Roboto, sans-serif !important;
}
.stApp { background: var(--yp-bg); }
.block-container { padding-top: 2.2rem; max-width: 1180px; }
.yp-appbar {
display: flex; align-items: center; gap: 14px;
background: #fff; padding: 18px 28px; border-radius: 16px;
border: 1px solid var(--yp-border);
box-shadow: 0 2px 12px rgba(20,30,80,.06); margin-bottom: 22px;
}
.yp-appbar img.yp-logo-img { height: 58px; display:block; }
.yp-appbar .yp-sub {
font-size: 13px; color: var(--yp-muted); margin-left: auto; font-weight: 600;
padding-left: 16px; border-left: 1px solid var(--yp-border);
}
div[data-testid="stVerticalBlockBorderWrapper"] {
background: var(--yp-card); border: 1px solid var(--yp-border) !important;
border-radius: 16px !important; padding: 6px 4px;
box-shadow: 0 2px 10px rgba(20,30,80,.05);
transition: box-shadow .18s ease, transform .18s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
box-shadow: 0 8px 24px rgba(30,107,255,.12); transform: translateY(-2px);
}
div[data-testid="stVerticalBlockBorderWrapper"] h3 { color: var(--yp-text); font-weight: 800; letter-spacing:-.4px; }
h2, .stSubheader, [data-testid="stHeading"] h2 { font-weight: 800 !important; letter-spacing:-.6px; color: var(--yp-text); }
.stButton > button {
border-radius: 10px; font-weight: 700; border: 1px solid var(--yp-border);
background: #fff; color: var(--yp-text); transition: all .15s ease;
}
.stButton > button:hover { border-color: var(--yp-brand); color: var(--yp-brand); }
.stButton > button[kind="primary"], .stFormSubmitButton > button {
background: var(--yp-brand); color: #fff; border: none; box-shadow: 0 4px 14px rgba(30,107,255,.3);
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover { background: var(--yp-brand-dark); color:#fff; }
a[data-testid="stBaseButton-secondary"], .stLinkButton a {
border-radius: 10px !important; font-weight: 700 !important;
border: 1px solid var(--yp-border) !important; background:#fff !important; color: var(--yp-brand) !important;
}
.stLinkButton a:hover { border-color: var(--yp-brand) !important; background:#F2F6FF !important; }
[data-testid="stCaptionContainer"] { color: var(--yp-muted); }
/* 상단 네비 탭 (Linkareer 풍) — 우측 정렬 + 파란 활성 탭 */
div[data-testid="stButtonGroup"] { justify-content: flex-end; gap: 6px; }
div[data-testid="stButtonGroup"] button {
border-radius: 9px !important; font-weight: 700 !important; padding: 4px 18px !important;
border: 1px solid var(--yp-border) !important; background: #fff !important; color: var(--yp-muted) !important;
}
div[data-testid="stButtonGroup"] button[aria-checked="true"],
div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"] {
background: var(--yp-brand) !important; color: #fff !important; border-color: var(--yp-brand) !important;
box-shadow: 0 3px 10px rgba(30,107,255,.28);
}
/* 입력 박스: 컨테이너 기준으로 라운드를 줘 password(아이콘 포함) 칸도 text 칸과 폭/모양 동일 */
div[data-baseweb="select"] > div, div[data-baseweb="input"], div[data-baseweb="base-input"] {
border-radius: 10px !important;
}
.stTextInput input, .stNumberInput input { border-radius: 10px !important; background: transparent !important; }
/* 브라우저 자동완성/포커스 시 배경색이 잠깐 노랗게/파랗게 튀는 것 방지 */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
input:-webkit-autofill:active {
-webkit-box-shadow: 0 0 0 1000px #fff inset !important;
-webkit-text-fill-color: var(--yp-text) !important;
caret-color: var(--yp-text) !important;
transition: background-color 99999s ease-in-out 0s !important;
}
#MainMenu, footer { visibility: hidden; }
</style>
"""
st.markdown(_YP_STYLE, unsafe_allow_html=True)

@st.cache_data
def _logo_data_uri() -> str:
    """헤더용 로고를 base64 data URI로 반환 (없으면 빈 문자열)."""
    for name in ("logo_header.png", "logo.png"):
        path = Path(__file__).resolve().parent / name
        if path.exists():
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:image/png;base64,{b64}"
    return ""


_logo_uri = _logo_data_uri()
# 상단 앱바는 제거하고 홈 화면 로고만 사용한다.

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"

def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

COMPANY_OPTIONS = [
    "SK하이닉스",
    "CJ ENM",
    "삼성전자",
    "네이버",
    "CJ제일제당",
    "현대자동차",
    "카카오",
    "LG전자",
    "삼성물산",
    "오뚜기",
]


@st.cache_data
def load_single_column_options(filename: str) -> list[str]:
    path = BASE_DIR / filename
    df = pd.read_csv(path, encoding="utf-8-sig")
    first_column = df.columns[0]
    values = df[first_column].dropna().astype(str).str.strip()
    return list(dict.fromkeys(value for value in values if value))


REGION_OPTIONS = [
    "서울", "인천", "대전", "대구", "부산", "광주", "울산", "경기", "강원", 
    "충남", "충북", "경북", "경남", "전남", "전북", "제주", "세종", "해외"
]

ROLE_OPTIONS = [
    "사업관리", "경영.회계.사무", "금융.보험", "교육.자연.사회과학", 
    "법률.경찰.소방.교도.국방", "보건.의료", "사회복지.종교", "문화.예술.디자인.방송", 
    "운전.운송", "영업판매", "경비.청소", "이용.숙박.여행.오락.스포츠", 
    "음식서비스", "건설", "기계", "재료", "화학", "섬유.의복", "전기.전자", 
    "정보통신", "식품가공", "인쇄.목재.가구.공예", "환경.에너지.안전", "농림어업", "연구"
]

EDUCATION_OPTIONS = [
    "학력무관", "중졸이하", "고졸", "대졸(2~3년)", "대졸(4년)", "석사", "박사"
]

SKILL_OPTIONS = load_single_column_options("보유 기술.csv")

# =========================
# session state
# =========================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "response_data" not in st.session_state:
    st.session_state.response_data = None

if "saved_events" not in st.session_state:
    st.session_state.saved_events = []

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "profile" not in st.session_state:
    st.session_state.profile = {}

if not st.session_state.logged_in:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            if _logo_uri:
                _login_head = (
                    "<div style='text-align:center;margin:6px 0 20px;'>"
                    f"<img src='{_logo_uri}' alt='YouthPath' style='height:72px;display:block;margin:0 auto 12px;'/>"
                    "<div style='font-size:18px;font-weight:700;color:#1A1F36;white-space:nowrap;'>시작하기</div>"
                    "</div>"
                )
            else:
                _login_head = "<h2 style='text-align:center;margin-bottom:20px;white-space:nowrap;'>YouthPath 시작하기</h2>"
            st.markdown(_login_head, unsafe_allow_html=True)
            tab_login, tab_signup = st.tabs(["로그인", "회원가입"])
            
            with tab_login:
                login_id = st.text_input("아이디", key="login_id")
                login_pw = st.text_input("비밀번호", type="password", key="login_pw")
                if st.button("로그인", use_container_width=True, type="primary"):
                    users = load_users()
                    if login_id in users and users[login_id]["password"] == login_pw:
                        st.session_state.logged_in = True
                        st.session_state.current_user = login_id
                        st.session_state.profile = users[login_id].get("profile", {})
                        st.session_state.saved_events = users[login_id].get("saved_events", [])
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
                        
            with tab_signup:
                signup_id = st.text_input("아이디", key="signup_id")
                signup_pw = st.text_input("비밀번호", type="password", key="signup_pw")
                signup_pw_confirm = st.text_input("비밀번호 확인", type="password", key="signup_pw_confirm")
                if st.button("회원가입", use_container_width=True, type="primary"):
                    users = load_users()
                    if signup_id in users:
                        st.error("이미 존재하는 아이디입니다.")
                    elif signup_pw != signup_pw_confirm:
                        st.error("비밀번호가 일치하지 않습니다.")
                    elif len(signup_id) < 1 or len(signup_pw) < 1:
                        st.error("아이디와 비밀번호를 입력해주세요.")
                    else:
                        users[signup_id] = {
                            "password": signup_pw,
                            "profile": {},
                            "saved_events": []
                        }
                        save_users(users)
                        st.success("회원가입이 완료되었습니다. 로그인 탭에서 로그인해주세요.")
                        
    st.stop()

def add_event_to_calendar(event):
    exists = any(
        saved_event["title"] == event["title"]
        and saved_event["date"] == event["date"]
        for saved_event in st.session_state.saved_events
    )

    if exists:
        st.toast("이미 마이페이지에 추가된 항목이에요.", icon="ℹ️")
        return

    st.session_state.saved_events.append(event)
    users = load_users()
    if st.session_state.current_user in users:
        users[st.session_state.current_user]["saved_events"] = st.session_state.saved_events
        save_users(users)
    # 페이지 이동 없이 현재 화면 유지 + 토스트로 피드백 (MyPage 탭에서 확인)
    st.toast("마이페이지에 추가했어요. 📅", icon="✅")

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
    users = load_users()
    if st.session_state.current_user in users:
        users[st.session_state.current_user]["saved_events"] = st.session_state.saved_events
        save_users(users)

    st.rerun()

# =========================
# Sidebar
# =========================

with st.sidebar:

    st.subheader("👤 프로필")

    user_profile = st.session_state.profile

    def get_idx(options, val, default=0):
        try: return options.index(val)
        except ValueError: return default

    age = st.selectbox(
        "나이",
        list(range(19, 40)),
        index=get_idx(list(range(19, 40)), user_profile.get("age", 27), 8)
    )

    region_options = REGION_OPTIONS
    region = st.selectbox(
        "거주지",
        region_options,
        index=get_idx(region_options, user_profile.get("region", "서울"), region_options.index("서울") if "서울" in region_options else 0)
    )

    income_options = [f"중위 {percent}% 이하" for percent in range(10, 101, 10)]
    income = st.selectbox(
        "소득 구간",
        income_options,
        index=get_idx(income_options, user_profile.get("income", "중위 60% 이하"), 5)
    )

    edu_options = EDUCATION_OPTIONS
    education = st.selectbox(
        "학력",
        edu_options,
        index=get_idx(edu_options, user_profile.get("education", "대졸(4년)"), 4)
    )

    saved_skills = user_profile.get("skills", [option for option in ["정보처리기사", "SQLD", "Python"] if option in SKILL_OPTIONS])
    skills = st.multiselect(
        "보유 기술 / 자격증 / Tool",
        SKILL_OPTIONS,
        default=[s for s in saved_skills if s in SKILL_OPTIONS]
    )

    exp_options = [0,1,2,3,4,5]
    experience = st.selectbox(
        "경력(년)",
        exp_options,
        index=get_idx(exp_options, user_profile.get("experience", 0), 0)
    )

    saved_roles = user_profile.get("target_roles", [])
    target_roles = st.multiselect(
        "희망 직무",
        ROLE_OPTIONS,
        default=[r for r in saved_roles if r in ROLE_OPTIONS]
    )

    saved_companies = user_profile.get("target_companies", [])
    target_companies = st.multiselect(
        "관심 기업",
        COMPANY_OPTIONS,
        default=[c for c in saved_companies if c in COMPANY_OPTIONS]
    )

    if st.button("💾 프로필 저장", use_container_width=True):
        users = load_users()
        users[st.session_state.current_user]["profile"] = {
            "age": age,
            "region": region,
            "income": income,
            "education": education,
            "skills": skills,
            "experience": experience,
            "target_roles": target_roles,
            "target_companies": target_companies
        }
        save_users(users)
        st.session_state.profile = users[st.session_state.current_user]["profile"]
        st.success("프로필이 성공적으로 저장되었습니다.")

    st.divider()

    st.write(f"반갑습니다, **{st.session_state.current_user}**님!")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.profile = {}
        st.session_state.saved_events = []
        st.session_state.page = "home"
        st.rerun()

# =========================
# 상단 우측 네비게이션 (Linkareer 풍 탭) — 화면 전환만(rerun)이라 결과는 유지된다.
# key를 주지 않아 매 rerun마다 현재 page를 기본 선택으로 반영한다.
# =========================
_nav_map = {"Home": "home", "MyPage": "mypage"}
_rev_nav = {v: k for k, v in _nav_map.items()}
_cur_label = _rev_nav.get(st.session_state.page, "Home")
_nav_spacer, _nav_col = st.columns([5, 1.2])
with _nav_col:
    _choice = st.segmented_control(
        "nav",
        list(_nav_map.keys()),
        default=_cur_label,
        label_visibility="collapsed",
    )
if _choice and _nav_map[_choice] != st.session_state.page:
    st.query_params.clear()
    st.session_state.page = _nav_map[_choice]
    st.rerun()


def render_results(data: dict) -> None:
    """질문 결과(답변 + 정책/채용/자소서/일정 카드)를 현재 Home 화면에 렌더링한다."""
    used_agents = []
    if data.get("policy"): used_agents.append("Policy")
    if data.get("job"): used_agents.append("Job")
    if data.get("resume"): used_agents.append("Resume")
    if data.get("calendar"): used_agents.append("Calendar")
    c_done, c_btn, _c_sp = st.columns([2.6, 1.6, 3.5])
    with c_done:
        if used_agents:
            st.success("검색 완료!")
        else:
            st.warning("결과 없음")
    with c_btn:
        if st.button("🔎 검색 결과보기", use_container_width=True):
            st.session_state.show_answer = not st.session_state.get("show_answer", False)

    # 답변과 정책/채용 결과 카드 모두 '검색 결과보기'를 눌러야 표시된다.
    if not st.session_state.get("show_answer"):
        return

    st.subheader("💬 답변")
    st.write(data.get("answer", ""))

    # 정책 결과
    if data.get("policy"):
        st.subheader("📋 정책 결과")
        for item in data.get("policy", []):
            with st.container(border=True):
                st.markdown(f"### {item.get('title', '제목 없음')}")
                st.write(item.get("description", "정책 상세 내용을 확인해보세요."))
                deadline = item.get("deadline", "미정")
                st.caption(f"마감 날짜: {deadline}")
                col1, col2 = st.columns(2)
                with col1:
                    link_url = (
                        item.get("link") or item.get("url") or item.get("rqutUrla")
                        or item.get("rfcSiteUrla1") or item.get("rfcSiteUrla2") or "#"
                    )
                    link_kind = item.get("link_kind", "")
                    search_url = item.get("search_url", "")
                    # 신청(apply) URL이거나, info여도 로그인 요구 패턴이면 정부24 검색으로 우회
                    is_login_prone = any(p in link_url for p in _LOGIN_PRONE)
                    if link_kind == "apply" or link_url == "#" or is_login_prone:
                        nav_url = search_url or (
                            "https://www.gov.kr/search?srhQuery=" + quote(item.get("title", ""))
                        )
                        nav_label = "🔎 정부24에서 자세히 보기"
                    else:
                        nav_url = link_url
                        nav_label = "ℹ️ 자세히 보기"
                    if nav_url:
                        st.link_button(nav_label, nav_url, use_container_width=True)
                    else:
                        st.caption("🔗 연결 가능한 링크가 없어요.")
                    link_url = nav_url or ""
                with col2:
                    if st.button("➕ 마이페이지 추가", key=f"policy_calendar_{item.get('title', '')}", use_container_width=True):
                        if link_kind == "apply" and search_url:
                            save_link = search_url
                        elif link_url != "#":
                            save_link = link_url
                        else:
                            save_link = search_url
                        add_event_to_calendar({"title": item.get("title", ""), "date": deadline, "type": "정책", "source": "policy", "link": save_link})

    # 채용 결과
    if data.get("job"):
        st.subheader("💼 채용 결과")
        for item in data.get("job", []):
            with st.container(border=True):
                company = item.get("company", "")
                title = item.get("title", "")
                display_title = f"{company} - {title}" if company else title
                st.markdown(f"### {display_title}")
                st.write(item.get("description", "채용 상세 내용과 지원 자격을 확인해보세요."))
                deadline = item.get("deadline", item.get("date", "미정"))
                st.caption(f"마감 날짜: {deadline}")
                col1, col2 = st.columns(2)
                job_link = item.get("url") or item.get("link") or ""
                _jl_label, _jl_url = _job_link_safe(job_link, display_title)
                with col1:
                    if _jl_url:
                        st.link_button(_jl_label, _jl_url, use_container_width=True)
                    else:
                        st.caption("🔗 연결 링크 없음")
                with col2:
                    if st.button("➕ 마이페이지 추가", key=f"job_calendar_{company}_{title}", use_container_width=True):
                        add_event_to_calendar({"title": display_title, "date": deadline, "type": "채용", "source": "job", "link": _jl_url or ""})

    # 자소서 코치 결과
    if data.get("resume"):
        st.subheader("🎯 자소서 코치 (작성 프롬프트)")
        for i, item in enumerate(data.get("resume", [])):
            with st.container(border=True):
                company = item.get("company", "회사명 없음")
                target_role = item.get("target_role", "직무 없음")
                st.markdown(f"### 📌 {company} — {target_role} 작성 프롬프트")
                summary = item.get("company_summary", {})
                if isinstance(summary, dict):
                    st.markdown("**[회사 컨텍스트]**")
                    if summary.get("business_keywords"):
                        st.write(f"• 키워드: {', '.join(summary.get('business_keywords', []))}")
                    if summary.get("values"):
                        st.write(f"• 인재상: {', '.join(summary.get('values', []))}")
                elif isinstance(summary, str):
                    st.markdown("**[회사 컨텍스트]**")
                    st.write(summary)
                generated_prompt = item.get("generated_prompt", "")
                if generated_prompt:
                    st.markdown("**[합성된 프롬프트]**")
                    st.code(generated_prompt, language="markdown")

    # 마감 일정 결과
    if data.get("calendar"):
        st.subheader("📅 마감 일정")
        for i, item in enumerate(data.get("calendar", [])):
            with st.container(border=True):
                title = item.get("title", "일정")
                st.markdown(f"### {title}")
                deadline = item.get("deadline", item.get("date", "미정"))
                days_rem = item.get("days_remaining", "")
                d_day_str = f"D-{days_rem}" if days_rem != "" else ""
                st.caption(f"마감 날짜: {deadline} {f'({d_day_str})' if d_day_str else ''}")
                col1, col2 = st.columns(2)
                link_url = item.get("link") or item.get("url") or ""
                with col1:
                    if link_url:
                        st.link_button("🌐 사이트 바로가기", link_url, use_container_width=True)
                    else:
                        st.caption("🔗 연결 링크 없음")
                with col2:
                    if st.button("➕ 마이페이지 추가", key=f"cal_calendar_{i}_{title}", use_container_width=True):
                        add_event_to_calendar({"title": title, "date": deadline, "type": "일정", "source": "other", "link": link_url})


# =========================
# HOME PAGE
# =========================

if st.session_state.page == "home":

    if _logo_uri:
        st.markdown(
            "<div style='display:flex;align-items:center;gap:18px;margin:6px 0 22px;flex-wrap:wrap;'>"
            f"<img src='{_logo_uri}' alt='YouthPath' style='height:100px;display:block;'/>"
            "<span style='font-size:16px;color:#6B7280;font-weight:600;'>청년 사회진입 통합 서비스</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.title("YouthPath")
        st.caption("청년 사회진입 통합 서비스")

    # 폼으로 감싸 입력칸에서 Enter를 치면 바로 검색되게 한다.
    with st.form("ask_form", clear_on_submit=False):
        query = st.text_input(
            "질문",
            placeholder="예: 서울 청년 월세 정책 알려줘.",
            label_visibility="collapsed",
        )
        _submitted = st.form_submit_button("🔍 질문하기", type="primary")

    if _submitted:
        if not (query or "").strip():
            st.warning("질문을 입력해 주세요.")
            st.stop()

        target_role = ", ".join(target_roles)
        target_company = ", ".join(target_companies)

        try:
            with st.spinner("정책·채용·자소서·일정을 분석하는 중이에요... (최대 1분 정도 걸릴 수 있어요)"):
                response = requests.post(
                    "http://127.0.0.1:8000/ask",
                    json={
                        "query": query,
                        "profile": {
                            "age": age,
                            "region": region,
                            "income": income,
                            "education": education,
                            "skills": skills,
                            "experience": experience,
                            "experience_y": experience,
                            "target_role": target_role,
                            "target_roles": target_roles,
                            "target_company": target_company,
                            "target_companies": target_companies
                        }
                    },
                    timeout=120,
                )
                response.raise_for_status()
                response_data = response.json()
        except requests.exceptions.Timeout:
            st.error("⏱️ 응답이 너무 오래 걸려요. 잠시 후 다시 시도해 주세요.")
            st.stop()
        except requests.exceptions.ConnectionError:
            st.error("🔌 백엔드(FastAPI)에 연결할 수 없어요. 서버가 실행 중인지 확인해 주세요 (http://127.0.0.1:8000).")
            st.stop()
        except Exception as exc:  # noqa: BLE001
            st.error(f"요청 처리 중 오류가 발생했어요: {exc}")
            st.stop()

        # --- 터미널 디버깅 출력 ---
        print("\n" + "="*60)
        print("🛠️ [디버깅] 각 Agent별 응답 JSON 데이터")
        print("="*60)
        for agent_name in ["policy", "job", "resume", "calendar"]:
            if response_data.get(agent_name):
                print(f"\n[{agent_name.upper()} AGENT]")
                print(json.dumps(response_data[agent_name], ensure_ascii=False, indent=2))
        print("="*60 + "\n")

        st.session_state.response_data = response_data
        # 같은 Home 화면에 결과를 펼친다 (별도 페이지로 이동하지 않음)
        st.rerun()

    try:
        if "cal_year" in st.query_params:
            st.session_state.calendar_year = int(st.query_params["cal_year"])
        if "cal_month" in st.query_params:
            st.session_state.calendar_month = int(st.query_params["cal_month"])
        if "cal_day" in st.query_params:
            st.session_state.selected_day = int(st.query_params["cal_day"])
    except ValueError:
        pass

    # 같은 Home 화면: 질문 결과가 있으면 그 아래에 펼치고, 없으면 예시/안내를 보여준다.
    if st.session_state.get("response_data"):
        render_results(st.session_state.response_data)
    else:
        st.markdown("### 💡 예시 질문")
        st.markdown("""
        - 청년 주거 지원 정책 뭐가 있어?
        - 데이터 분석가 신입 공고 추천해줘
        - 네이버 자소서 어떻게 써야 할까?
        - 이번 달 신청 마감 임박한 거 정리해줘
        - 서울에서 월세 도와주는 정책이랑 IT 신입 공고 알려줘
        """)
        st.info("""
**📘 사용 방법**

프로필 정보를 입력한 뒤 질문을 입력하세요.
""")

# =========================
# MY PAGE
# =========================

elif st.session_state.page == "mypage":
    render_mypage()
