import calendar
from datetime import datetime

import streamlit as st


def render_mypage(saved_events=None, add_event_callback=None, delete_event_callback=None):
    st.title("🗓️ 마이페이지")

    today = datetime.today()
    saved_events = saved_events if saved_events is not None else st.session_state.get("saved_events", [])

    if "calendar_year" not in st.session_state:
        st.session_state.calendar_year = today.year

    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = today.month

    year = st.session_state.calendar_year
    month = st.session_state.calendar_month

    events = []
    for saved_event in saved_events:
        try:
            event_date = datetime.strptime(saved_event["date"], "%Y-%m-%d")
        except (KeyError, TypeError, ValueError):
            continue

        if event_date.year == year and event_date.month == month:
            d_day_num = (event_date.date() - today.date()).days
            d_day = f"D-{d_day_num}" if d_day_num >= 0 else f"D+{abs(d_day_num)}"
            events.append({
                **saved_event,
                "day": event_date.day,
                "d_day": d_day,
                "days_remaining": d_day_num,
            })

    events.sort(key=lambda event: event["days_remaining"])

    events_by_day = {}
    for event in events:
        events_by_day.setdefault(event["day"], []).append(event)

    if "selected_day" not in st.session_state:
        st.session_state.selected_day = today.day

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

    left, right = st.columns([3, 1.35])

    with left:
        weekdays = ["일", "월", "화", "수", "목", "금", "토"]

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
                            unsafe_allow_html=True,
                        )
                        continue

                    if st.button(str(day), key=f"day_{day}"):
                        st.session_state.selected_day = day
                        st.rerun()

                    for event in events_by_day.get(day, []):
                        if event.get("source") == "policy":
                            st.markdown("🔴 정책")
                        elif event.get("source") == "job":
                            st.markdown("🔵 채용")
                        else:
                            st.markdown("⚪ 일정")

        st.caption("🔴 정책 마감  |  🔵 채용 마감  |  ⚪ 직접 추가")

    with right:
        selected_day = st.session_state.selected_day
        selected_events = events_by_day.get(selected_day, [])

        st.error(f"📅 선택: {year}-{month:02d}-{selected_day:02d}")

        with st.container(border=True):
            st.markdown("### ➕ 직접 일정 추가")

            custom_title = st.text_input(
                "일정 제목",
                placeholder="예: 포트폴리오 제출 마감",
            )

            safe_day = min(selected_day, calendar.monthrange(year, month)[1])
            custom_date = st.date_input(
                "일정 날짜",
                value=datetime(year, month, safe_day).date(),
            )

            custom_link = st.text_input(
                "관련 링크",
                placeholder="https://...",
            )

            if st.button("직접 추가하기"):
                event = {
                    "title": custom_title or "직접 추가 일정",
                    "date": custom_date.strftime("%Y-%m-%d"),
                    "type": "직접 추가",
                    "source": "manual",
                    "link": custom_link,
                }
                if add_event_callback:
                    add_event_callback(event)
                else:
                    st.session_state.setdefault("saved_events", []).append(event)
                    st.rerun()

        with st.container(border=True):
            st.markdown(f"### ▼ 그 날의 이벤트 ({len(selected_events)}건)")

            if selected_events:
                for event in selected_events:
                    st.markdown(f"**💼 {event['title']}**")
                    st.caption(f"마감: {event['date']} · {event['d_day']}")

                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.link_button("해당 사이트로 가기 →", event.get("link") or "https://www.youthcenter.go.kr")
                    with c2:
                        if st.button("삭제", key=f"delete_{event.get('source')}_{event['title']}_{event['date']}"):
                            if delete_event_callback:
                                delete_event_callback(event)
                            else:
                                st.session_state.saved_events = [
                                    saved
                                    for saved in st.session_state.get("saved_events", [])
                                    if not (
                                        saved.get("title") == event.get("title")
                                        and saved.get("date") == event.get("date")
                                        and saved.get("source") == event.get("source")
                                    )
                                ]
                                st.rerun()

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
                if event.get("source") == "policy":
                    color = "🟥"
                elif event.get("source") == "job":
                    color = "🟦"
                else:
                    color = "⬜"

                st.markdown(
                    f"{color} **{event['title']}** "
                    f"<span style='float:right'>{event['d_day']}</span>",
                    unsafe_allow_html=True,
                )

    st.divider()

    if st.button("🏠 홈으로 돌아가기"):
        st.session_state.page = "home"
        st.rerun()
