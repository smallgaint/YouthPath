import streamlit as st

def render_output_page():

    st.title("YouthPath")

    st.text_input(
        "",
        value=st.session_state.query
    )

    st.success("Router가 호출한 Agent : policy + job")

    st.subheader("💬 답변")

    st.info("""
서울 거주 27세 기준으로 결과를 정리했어요.

정책:
청년월세지원이 자격 요건을 모두 충족해 가장 유리합니다.

채용:
00회사 데이터분석 신입이 적합도 87%로 가장 유리합니다.
""")

    st.divider()

    st.subheader("📋 정책 결과")

    with st.container(border=True):

        st.markdown("### 청년월세지원")

        st.caption("마감: 2026-05-31")

        st.write("""
만 19~34세 무주택 청년에게 월 20만원씩 최대 12개월 지원
""")

        st.success("충족: 나이 27세, 서울 거주, 중위 60% 이하")

        col1, col2 = st.columns(2)

        with col1:
            st.link_button(
                "해당 사이트 가기",
                "https://youth.seoul.go.kr"
            )

        with col2:
            st.button("📅 달력에 추가하기")

    st.divider()

    if st.button("⬅ 다시 검색"):
        st.session_state.page = "input"
