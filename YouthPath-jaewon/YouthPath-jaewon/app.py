import streamlit as st
import requests
import pandas as pd
import calendar
import json
from datetime import datetime
from pathlib import Path
import streamlit.components.v1 as components
from html import escape
from frontend.components.mypage import render_mypage


st.set_page_config(
    page_title="YouthPath",
    layout="wide"
)

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
            st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>🎯 YouthPath 시작하기</h2>", unsafe_allow_html=True)
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

    if not exists:
        st.session_state.saved_events.append(event)
        users = load_users()
        if st.session_state.current_user in users:
            users[st.session_state.current_user]["saved_events"] = st.session_state.saved_events
            save_users(users)

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
    users = load_users()
    if st.session_state.current_user in users:
        users[st.session_state.current_user]["saved_events"] = st.session_state.saved_events
        save_users(users)

    st.rerun()

# =========================
# Sidebar
# =========================

with st.sidebar:

    st.title("🎓 YouthPath")
    st.caption("청년 사회진입 통합 AI 서비스")

    st.divider()

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

    if st.button("📅 마이페이지"):
        st.session_state.page = "mypage"

    if st.button("🏠 홈"):
        st.query_params.clear()
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
        target_role = ", ".join(target_roles)
        target_company = ", ".join(target_companies)

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
            }
        )

        response_data = response.json()
        
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

    try:
        if "cal_year" in st.query_params:
            st.session_state.calendar_year = int(st.query_params["cal_year"])
        if "cal_month" in st.query_params:
            st.session_state.calendar_month = int(st.query_params["cal_month"])
        if "cal_day" in st.query_params:
            st.session_state.selected_day = int(st.query_params["cal_day"])
    except ValueError:
        pass

    # =========================
    # Output
    # =========================

elif st.session_state.page == "output":
    if st.session_state.response_data:
        data = st.session_state.response_data
        st.title("📤 결과")
        
        used_agents = []
        if data.get("policy"): used_agents.append("Policy")
        if data.get("job"): used_agents.append("Job")
        if data.get("resume"): used_agents.append("Resume")
        if data.get("calendar"): used_agents.append("Calendar")
        
        if used_agents:
            st.success(f"Router가 {' + '.join(used_agents)} Agent를 선택했습니다.")
        else:
            st.warning("분석 결과 적절한 에이전트를 찾지 못했습니다.")
            
        st.subheader("💬 답변")
        st.write(data.get("answer", ""))

        # =========================
        # 정책 결과
        # =========================
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
                        # 정책 API의 원본 키가 넘어올 경우를 대비한 Fallback 탐색
                        link_url = (
                            item.get("link") or 
                            item.get("url") or 
                            item.get("rqutUrla") or 
                            item.get("rfcSiteUrla1") or 
                            item.get("rfcSiteUrla2") or "#"
                        )
                        st.link_button("🌐 사이트 바로가기", link_url, use_container_width=True)
                    with col2:
                        if st.button(
                            "➕ 마이페이지 추가",
                            key=f"policy_calendar_{item.get('title', '')}",
                            use_container_width=True
                        ):
                            add_event_to_calendar({
                                "title": item.get("title", ""),
                                "date": deadline,
                                "type": "정책",
                                "source": "policy",
                                "link": link_url if link_url != "#" else ""
                            })

        # =========================
        # 채용 결과
        # =========================
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
                    with col1:
                        link_url = item.get("url") or item.get("link") or "#"
                        st.link_button("🌐 사이트 바로가기", link_url, use_container_width=True)
                    with col2:
                        if st.button(
                            "➕ 마이페이지 추가",
                            key=f"job_calendar_{company}_{title}",
                            use_container_width=True
                        ):
                            add_event_to_calendar({
                                "title": display_title,
                                "date": deadline,
                                "type": "채용",
                                "source": "job",
                                "link": link_url if link_url != "#" else ""
                            })

        # =========================
        # 자소서 코치 결과 (이력서)
        # =========================
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

        # =========================
        # 일정 결과
        # =========================
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
                    with col1:
                        link_url = item.get("link") or item.get("url") or "#"
                        st.link_button("🌐 사이트 바로가기", link_url, use_container_width=True)
                    with col2:
                        if st.button(
                            "➕ 마이페이지 추가",
                            key=f"cal_calendar_{i}_{title}",
                            use_container_width=True
                        ):
                            add_event_to_calendar({
                                "title": title,
                                "date": deadline,
                                "type": "일정",
                                "source": "other",
                                "link": link_url if link_url != "#" else ""
                            })

        if st.button("🏠 홈으로 돌아가기"):
            st.query_params.clear()
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
    render_mypage()
