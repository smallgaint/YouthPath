import streamlit as st


def _agent_items(data, agent_name):
    result = data.get(agent_name)
    if isinstance(result, dict):
        return result.get("items", [])
    if isinstance(result, list):
        return result
    return []


def _agent_error(data, agent_name):
    result = data.get(agent_name)
    if isinstance(result, dict):
        return result.get("error")
    return None


def _criterion_text(criteria):
    labels = []
    for criterion in criteria or []:
        label = criterion.get("label", "조건")
        required = criterion.get("required", "")
        user_value = criterion.get("user_value", "")
        labels.append(f"{label}: {user_value} / {required}")
    return ", ".join(labels) if labels else "없음"


def _add_event(add_event_callback, event):
    if add_event_callback:
        add_event_callback(event)
    else:
        st.warning("캘린더 추가 함수가 연결되지 않았습니다.")


def render_output_page(data=None, add_event_callback=None):
    data = data or st.session_state.get("response_data")

    if not data:
        st.warning("아직 결과가 없습니다. 먼저 질문을 입력해주세요.")
        if st.button("홈으로 이동"):
            st.session_state.page = "home"
            st.rerun()
        return

    policy_items = _agent_items(data, "policy")
    job_items = _agent_items(data, "job")
    resume_items = _agent_items(data, "resume")
    calendar_items = _agent_items(data, "calendar")
    called_agents = data.get("called_agents", [])

    st.title("📤 결과")
    if called_agents:
        st.success(f"Router가 호출한 Agent: {', '.join(called_agents)}")
    else:
        st.success("Router가 Policy + Job Agent를 선택했습니다.")

    st.subheader("💬 답변")
    st.write(data.get("answer", ""))

    st.subheader("📋 정책 결과")
    if _agent_error(data, "policy"):
        st.warning(_agent_error(data, "policy"))

    for item in policy_items:
        with st.container(border=True):
            st.markdown(f"### {item.get('title', '정책')}")
            st.caption(f"마감: {item.get('deadline') or '미정'}")
            st.write(item.get("summary") or item.get("description") or "")

            matched = _criterion_text(item.get("matched_criteria"))
            unmatched = _criterion_text(item.get("unmatched_criteria"))
            st.success(f"충족: {matched}")
            if unmatched != "없음":
                st.warning(f"확인 필요: {unmatched}")

            col1, col2 = st.columns(2)
            with col1:
                st.link_button("해당 사이트 가기", item.get("link") or "https://youth.seoul.go.kr")
            with col2:
                if st.button("📅 캘린더 추가하기", key=f"policy_calendar_{item.get('policy_id', item.get('title'))}"):
                    _add_event(add_event_callback, {
                        "title": item.get("title", "정책 마감"),
                        "date": item.get("deadline"),
                        "type": "정책",
                        "source": "policy",
                        "link": item.get("link") or "",
                    })

    st.subheader("💼 채용 결과")
    if _agent_error(data, "job"):
        st.warning(_agent_error(data, "job"))

    for item in job_items:
        with st.container(border=True):
            st.markdown(f"### {item.get('company', '회사')}")
            st.write(item.get("title", ""))

            fit_score = item.get("fit_score")
            deadline = item.get("deadline") or item.get("date", "")
            if fit_score is not None:
                st.caption(f"적합도 {int(float(fit_score) * 100)}% · {item.get('location', '')} · 마감 {deadline}")

            days_remaining = item.get("days_remaining")
            st.warning(f"D-{days_remaining}" if days_remaining is not None else deadline)

            col1, col2 = st.columns(2)
            with col1:
                st.link_button("해당 사이트 가기", item.get("url") or item.get("link") or "https://www.work.go.kr")
            with col2:
                if st.button("📅 캘린더 추가하기", key=f"job_calendar_{item.get('wantedAuthNo', item.get('title'))}"):
                    _add_event(add_event_callback, {
                        "title": f"{item.get('company', '')} {item.get('title', '')}".strip(),
                        "date": deadline,
                        "type": "채용",
                        "source": "job",
                        "link": item.get("url") or item.get("link") or "",
                    })

    if resume_items or _agent_error(data, "resume"):
        st.subheader("✍ 자소서 가이드")
        if _agent_error(data, "resume"):
            st.warning(_agent_error(data, "resume"))

        for item in resume_items:
            with st.container(border=True):
                st.markdown(f"### {item.get('company', '기업')} 자소서 가이드")

                keywords = item.get("emphasize_keywords", [])
                keyword_text = ", ".join(keyword.get("keyword", str(keyword)) for keyword in keywords)
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

    if calendar_items or _agent_error(data, "calendar"):
        st.subheader("📅 마감 일정")
        if _agent_error(data, "calendar"):
            st.warning(_agent_error(data, "calendar"))

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
                    st.link_button("해당 사이트 가기", item.get("link") or "https://www.youthcenter.go.kr")
                with col2:
                    if st.button("📅 캘린더 추가하기", key=f"calendar_add_{item.get('event_id', item.get('title'))}"):
                        _add_event(add_event_callback, {
                            "title": item.get("title", "마감 일정"),
                            "date": deadline,
                            "type": "일정",
                            "source": item.get("source", "calendar"),
                            "link": item.get("link") or "",
                        })

    if st.button("🏠 홈으로 돌아가기"):
        st.session_state.page = "home"
        st.rerun()
