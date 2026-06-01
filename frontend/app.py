import streamlit as st
import requests
import pandas as pd
import calendar
from datetime import datetime

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

API_BASE_URL = "http://127.0.0.1:8000"

def agent_items(data, agent_name):
    result = data.get(agent_name)
    if isinstance(result, dict):
        return result.get("items", [])
    if isinstance(result, list):
        return result
    return []

def agent_error(data, agent_name):
    result = data.get(agent_name)
    if isinstance(result, dict):
        return result.get("error")
    return None

def criterion_text(criteria):
    labels = []
    for criterion in criteria or []:
        label = criterion.get("label", "조건")
        required = criterion.get("required", "")
        user_value = criterion.get("user_value", "")
        labels.append(f"{label}: {user_value} / {required}")
    return ", ".join(labels) if labels else "없음"

def event_from_policy(item):
    return {
        "title": item.get("title", "정책 마감"),
        "date": item.get("deadline"),
        "type": "정책",
        "source": "policy",
        "link": item.get("link") or ""
    }

def event_from_job(item):
    return {
        "title": f"{item.get('company', '')} {item.get('title', '')}".strip(),
        "date": item.get("deadline"),
        "type": "채용",
        "source": "job",
        "link": item.get("url") or item.get("link") or ""
    }

def event_from_calendar(item):
    return {
        "title": item.get("title", "마감 일정"),
        "date": item.get("deadline") or item.get("date"),
        "type": "일정",
        "source": item.get("source", "calendar"),
        "link": item.get("link") or ""
    }

def add_event_to_calendar(event):
    if not event.get("date"):
        st.warning("마감일이 없는 항목은 캘린더에 추가할 수 없습니다.")
        return

    exists = any(
        saved_event["title"] == event["title"]
        and saved_event["date"] == event["date"]
        for saved_event in st.session_state.saved_events
    )

    if not exists:
        st.session_state.saved_events.append(event)

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

    region = st.selectbox(
        "거주지",
        ["서울", "경기", "인천", "부산", "대구"]
    )

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

    skills = st.multiselect(
        "보유 기술",
        [
            "Python",
            "SQL",
            "React",
            "Java",
            "Excel"
        ],
        default=["Python", "SQL"]
    )

    experience = st.selectbox(
        "경력(년)",
        [0,1,2,3,4,5]
    )

    target_role = st.selectbox(
        "희망 직무",
        [
            "데이터 분석가",
            "백엔드 개발자",
            "프론트엔드 개발자",
            "기획",
            "마케팅"
        ]
    )

    target_company = st.selectbox(
        "관심 기업",
        [
            "네이버",
            "카카오",
            "삼성",
            "쿠팡",
            "토스"
        ]
    )

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

        try:
            response = requests.post(
                f"{API_BASE_URL}/ask",
                json={
                    "query": query,
                    "profile": {
                        "age": age,
                        "region": region,
                        "income": income,
                        "education": education,
                        "skills": skills,
                        "experience": experience,
                        "target_role": target_role,
                        "target_company": target_company
                    }
                },
                timeout=20
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            st.error(f"백엔드 연결에 실패했습니다: {exc}")
        else:
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
        policy_items = agent_items(data, "policy")
        job_items = agent_items(data, "job")
        resume_items = agent_items(data, "resume")
        calendar_items = agent_items(data, "calendar")
        called_agents = data.get("called_agents", [])

        st.title("📤 결과")
        if called_agents:
            st.success(f"Router가 호출한 Agent: {', '.join(called_agents)}")
        else:
            st.success("Router가 Policy + Job Agent를 선택했습니다.")
        st.subheader("💬 답변")
        st.write(data["answer"])

        # =========================
        # 정책 결과
        # =========================

        st.subheader("📋 정책 결과")

        if agent_error(data, "policy"):
            st.warning(agent_error(data, "policy"))

        for item in policy_items:

            with st.container(border=True):

                st.markdown(f"### {item['title']}")
                st.caption(f"마감: {item['deadline']}")

                st.write(item.get("summary") or item.get("description") or "")

                matched = criterion_text(item.get("matched_criteria"))
                unmatched = criterion_text(item.get("unmatched_criteria"))
                st.success(f"충족: {matched}")
                if unmatched != "없음":
                    st.warning(f"확인 필요: {unmatched}")

                col1, col2 = st.columns(2)

                with col1:
                    st.link_button(
                        "해당 사이트 가기",
                        item.get("link") or "https://youth.seoul.go.kr"
                    )

                with col2:
                    if st.button(
                        "📅 캘린더 추가하기",
                        key=f"policy_calendar_{item['title']}"
                    ):
                        add_event_to_calendar(event_from_policy(item))

        # =========================
        # 채용 결과
        # =========================

        st.subheader("💼 채용 결과")

        if agent_error(data, "job"):
            st.warning(agent_error(data, "job"))

        for item in job_items:

            with st.container(border=True):

                st.markdown(f"### {item['company']}")
                st.write(item["title"])

                fit_score = item.get("fit_score")
                deadline = item.get("deadline") or item.get("date", "")
                if fit_score is not None:
                    st.caption(f"적합도 {int(float(fit_score) * 100)}% · {item.get('location', '')} · 마감 {deadline}")
                st.warning(f"D-{item.get('days_remaining')}" if item.get("days_remaining") is not None else deadline)

                col1, col2 = st.columns(2)

                with col1:
                    st.link_button(
                        "해당 사이트 가기",
                        item.get("url") or item.get("link") or "https://www.work.go.kr"
                        )

                with col2:
                    if st.button(
                        "📅 캘린더 추가하기",
                        key=f"job_calendar_{item['company']}_{item['title']}"
                    ):
                        add_event_to_calendar(event_from_job(item))

        # =========================
        # 자소서 결과
        # =========================

        if resume_items or agent_error(data, "resume"):
            st.subheader("✍ 자소서 가이드")

            if agent_error(data, "resume"):
                st.warning(agent_error(data, "resume"))

            for item in resume_items:
                with st.container(border=True):
                    st.markdown(f"### {item.get('company', '기업')} 자소서 가이드")

                    keywords = item.get("emphasize_keywords", [])
                    keyword_text = ", ".join(
                        keyword.get("keyword", str(keyword))
                        for keyword in keywords
                    )
                    st.write(f"강조 키워드: {keyword_text or '없음'}")

                    matching_points = item.get("matching_points", [])
                    if matching_points:
                        st.caption("매칭 포인트")
                        for point in matching_points:
                            st.write(
                                f"- {point.get('user_skill')} ↔ {point.get('company_keyword')} "
                                f"({int(float(point.get('fit_score', 0)) * 100)}%)"
                            )

                    gaps = item.get("evidence_gaps", [])
                    st.write(f"보강 제안: {', '.join(gaps) if gaps else '없음'}")

                    angles = item.get("story_angles", [])
                    if angles:
                        st.caption("Story Angle")
                        for angle in angles:
                            st.write(f"- {angle}")

        # =========================
        # 마감 일정
        # =========================

        if calendar_items or agent_error(data, "calendar"):
            st.subheader("📅 마감 일정")

            if agent_error(data, "calendar"):
                st.warning(agent_error(data, "calendar"))

            for item in calendar_items:
                with st.container(border=True):
                    deadline = item.get("deadline") or item.get("date", "")
                    days_remaining = item.get("days_remaining")
                    st.markdown(f"### {item.get('title', '마감 일정')}")
                    st.caption(f"마감: {deadline}")
                    if days_remaining is not None:
                        st.warning(f"D-{days_remaining}" if days_remaining >= 0 else f"D+{abs(days_remaining)}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.link_button(
                            "해당 사이트 가기",
                            item.get("link") or "https://www.youthcenter.go.kr"
                        )
                    with col2:
                        if st.button(
                            "📅 캘린더 추가하기",
                            key=f"calendar_add_{item.get('event_id', item.get('title', 'event'))}"
                        ):
                            add_event_to_calendar(event_from_calendar(item))

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
                                height: 95px;
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

                        border_color = "#ff4b4b" if is_selected else "#eeeeee"
                        bg_color = "#fff3f3" if is_selected else "white"

                        # 날짜 선택 버튼
                        if st.button(str(day), key=f"day_{day}"):
                            st.session_state.selected_day = day
                            st.rerun()

                        # 이벤트 표시
                        if has_events:
                            for event in events_by_day[day]:
                                if event["source"] == "policy":
                                    st.markdown("🔴 정책")
                                elif event["source"] == "job":
                                    st.markdown("🔵 채용")
                                else:
                                    st.markdown("⚪ 일정")

        st.caption("🔴 정책 마감  |  🔵 채용 마감  |  ⚪ 직접 추가")

    # =========================
    # 오른쪽: 선택 날짜 패널
    # =========================
    with right:

        selected_day = st.session_state.selected_day
        selected_events = events_by_day.get(selected_day, [])

        st.error(f"📅 선택: {year}-{month:02d}-{selected_day:02d}")

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
                    "link": custom_link
                })

        with st.container(border=True):
            st.markdown(f"### ▼ 그 날의 이벤트 ({len(selected_events)}건)")

            if selected_events:
                for event in selected_events:
                    st.markdown(f"**💼 {event['title']}**")
                    st.caption(f"마감: {event['date']} · {event['d_day']}")

                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.link_button("해당 사이트로 가기 →", event["link"])
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

        with st.container(border=True):
            st.markdown("### 📌 이번 달 이벤트 리스트")

            for event in events:
                if event["source"] == "policy":
                    color = "🟥"
                elif event["source"] == "job":
                    color = "🟦"
                else:
                    color = "⬜"

                st.markdown(
                    f"{color} **{event['title']}** "
                    f"<span style='float:right'>{event['d_day']}</span>",
                    unsafe_allow_html=True
                )

    st.divider()

    if st.button("🏠 홈으로 돌아가기"):
        st.session_state.page = "home"
        st.rerun()
