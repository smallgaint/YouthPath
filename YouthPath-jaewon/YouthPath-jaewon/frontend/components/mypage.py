import streamlit as st
import calendar
from datetime import datetime

def render_mypage():

    st.title("📅 내 일정 달력")

    now = datetime.now()

    year = now.year
    month = now.month

    st.subheader(f"{year}.{month}")

    cal = calendar.monthcalendar(year, month)

    cols = st.columns(7)

    days = ["일", "월", "화", "수", "목", "금", "토"]

    for i, day in enumerate(days):
        cols[i].markdown(f"**{day}**")

    for week in cal:

        cols = st.columns(7)

        for i, day in enumerate(week):

            if day == 0:
                cols[i].write("")

            else:
                if day == 20:
                    cols[i].error(f"{day}\n\n데이터분석 지원")

                elif day == 31:
                    cols[i].warning(f"{day}\n\n청년월세지원")

                else:
                    cols[i].write(str(day))

    st.divider()

    st.subheader("📌 이번 달 이벤트")

    st.markdown("""
- 데이터분석 신입 지원 (D-8)
- 청년월세지원 마감 (D-19)
""")

    if st.button("⬅ 메인으로"):
        st.session_state.page = "input"
