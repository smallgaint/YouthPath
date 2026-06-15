import calendar
import json
from datetime import date, datetime
from pathlib import Path
from html import escape
from urllib.parse import quote


# 로그인/본인인증을 요구하는 정부 포털 경로 패턴 (해당 시 정부24 검색으로 우회)
_LOGIN_PRONE = ("ai-recruit", "moveTWAT", "rcvfvrSvc", "savingsAccount", "/ssis-tbu/", "login", "khug.or.kr")


def event_link_safe(event):
    """이벤트 링크를 반환하되, 로그인 요구 URL이면 정부24 검색으로 우회한다.
    반환: (라벨, URL) 또는 (None, None)."""
    link = (event.get("link") or "").strip()
    title = (event.get("title") or "").strip()
    if link and not any(p in link for p in _LOGIN_PRONE):
        return "해당 사이트로 가기 →", link
    if title:
        return "🔎 정부24에서 검색", "https://www.gov.kr/search?srhQuery=" + quote(title)
    return None, None

import streamlit as st
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USERS_FILE = BASE_DIR / "users.json"

def sync_events_to_db():
    if "current_user" in st.session_state and st.session_state.current_user:
        if USERS_FILE.exists():
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
            if st.session_state.current_user in users:
                users[st.session_state.current_user]["saved_events"] = st.session_state.saved_events
                with open(USERS_FILE, "w", encoding="utf-8") as f:
                    json.dump(users, f, ensure_ascii=False, indent=4)

EVENT_TYPES = {
    "policy": {"label": "정책 마감", "short": "정책", "dot": "policy"},
    "job": {"label": "채용 마감", "short": "채용", "dot": "job"},
    "other": {"label": "기타", "short": "기타", "dot": "other"},
    "manual": {"label": "기타", "short": "기타", "dot": "other"},
}


def normalize_event_source(source):
    if source in ("policy", "job"):
        return source
    return "other"


def event_meta(event):
    return EVENT_TYPES.get(normalize_event_source(event.get("source")), EVENT_TYPES["other"])


def add_event_to_calendar(event):
    event["source"] = normalize_event_source(event.get("source"))
    event["type"] = EVENT_TYPES[event["source"]]["label"]

    exists = any(
        saved_event["title"] == event["title"]
        and saved_event["date"] == event["date"]
        and normalize_event_source(saved_event.get("source")) == event["source"]
        for saved_event in st.session_state.saved_events
    )

    if not exists:
        st.session_state.saved_events.append(event)
        sync_events_to_db()

    st.session_state.page = "mypage"
    st.rerun()


def delete_event_from_calendar(event):
    target_source = normalize_event_source(event.get("source"))
    st.session_state.saved_events = [
        saved_event
        for saved_event in st.session_state.saved_events
        if not (
            saved_event["title"] == event["title"]
            and saved_event["date"] == event["date"]
            and normalize_event_source(saved_event.get("source")) == target_source
        )
    ]
    sync_events_to_db()

    st.rerun()


def move_month(delta):
    year = st.session_state.calendar_year
    month = st.session_state.calendar_month + delta

    if month < 1:
        year -= 1
        month = 12
    elif month > 12:
        year += 1
        month = 1

    st.session_state.calendar_year = year
    st.session_state.calendar_month = month
    st.session_state.selected_day = min(
        st.session_state.selected_day,
        calendar.monthrange(year, month)[1],
    )
    st.rerun()


def build_events(year, month, today):
    events = []
    for saved_event in st.session_state.saved_events:
        date_str = saved_event.get("date") or ""
        date_str = str(date_str).strip()
        # 날짜가 없거나 '미정' 등 파싱 불가한 값이면 캘린더에서 건너뛴다.
        if not date_str or date_str in ("미정", "None"):
            continue
        event_date = None
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y.%m.%d", "%y-%m-%d", "%y%m%d"):
            try:
                event_date = datetime.strptime(date_str, fmt)
                saved_event["date"] = event_date.strftime("%Y-%m-%d")
                break
            except (ValueError, TypeError):
                pass

        if not event_date:
            continue

        if event_date.year == year and event_date.month == month:
            d_day_num = (event_date.date() - today).days
            d_day = f"D-{d_day_num}" if d_day_num >= 0 else f"D+{abs(d_day_num)}"

            events.append(
                {
                    **saved_event,
                    "source": normalize_event_source(saved_event.get("source")),
                    "day": event_date.day,
                    "d_day": d_day,
                }
            )

    return sorted(events, key=lambda event: (event["date"], event["title"]))


def render_calendar_grid(year, month, selected_day, events_by_day):
    calendar.setfirstweekday(calendar.SUNDAY)
    weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)
    weekdays = ["일", "월", "화", "수", "목", "금", "토"]

    cells = []
    for week in weeks:
        for current_date in week:
            is_current_month = current_date.month == month
            is_selected = (
                current_date.year == year
                and current_date.month == month
                and current_date.day == selected_day
            )
            day_events = events_by_day.get(current_date.day, []) if is_current_month else []

            classes = ["calendar-cell"]
            if not is_current_month:
                classes.append("is-muted")
            if is_selected:
                classes.append("is-selected")

            # 각 일정 칩도 클릭 가능 — 클릭하면 그 날짜가 선택된다 (셀 클릭과 동일 동작)
            event_tags = "".join(
                (
                    f"<span class='event-chip {event_meta(event)['dot']}' "
                    f"onclick=\"event.stopPropagation(); selectDay({current_date.year}, {current_date.month}, {current_date.day})\">"
                    f"{escape(event['title'])}"
                    "</span>"
                )
                for event in day_events[:3]
            )
            more_tag = ""
            if len(day_events) > 3:
                more_tag = f"<span class='event-more'>+{len(day_events) - 3}</span>"

            cells.append(
                f'<button class="{" ".join(classes)}" type="button" '
                f'onclick="selectDay({current_date.year}, {current_date.month}, {current_date.day})">'
                f'<span class="day-number">{current_date.day}</span>'
                f'<span class="event-stack">{event_tags}{more_tag}</span>'
                "</button>"
            )

    weekday_headers = "".join(
        f"<div class='weekday {'sun' if day == '일' else 'sat' if day == '토' else ''}'>{day}</div>"
        for day in weekdays
    )

    calendar_html = f"""<!doctype html>
    <html lang="ko">
    <head>
    <meta charset="utf-8">
        <style>
            html, body {{ margin: 0; padding: 0; font-family: "Source Sans Pro", system-ui, sans-serif; }}
            .calendar-shell {{
                border: 1px solid #d7dde8; border-radius: 8px; overflow: hidden;
                background: #ffffff; width: 100%;
            }}
            .calendar-weekdays, .calendar-grid {{
                display: grid; grid-template-columns: repeat(7, minmax(0, 1fr));
            }}
            .weekday {{
                height: 38px; display: flex; align-items: center; justify-content: center;
                border-right: 1px solid #d7dde8; border-bottom: 1px solid #d7dde8;
                background: #f7f9fc; color: #394150; font-size: 0.92rem; font-weight: 700;
            }}
            .weekday:last-child, .calendar-cell:nth-child(7n) {{ border-right: 0; }}
            .weekday.sun {{ color: #d64545; }}
            .weekday.sat {{ color: #2f6fdb; }}
            .calendar-cell {{
                width: 100%; min-height: 116px; height: 116px; padding: 10px;
                display: flex; flex-direction: column; gap: 8px; border: 0;
                border-right: 1px solid #d7dde8; border-bottom: 1px solid #d7dde8;
                background: #ffffff; color: #172033; cursor: pointer; text-align: left;
                box-sizing: border-box; font: inherit;
                transition: background 120ms ease, box-shadow 120ms ease;
            }}
            .calendar-cell:hover {{ background: #f4f8ff; box-shadow: inset 0 0 0 2px #8fb8ff; }}
            .calendar-cell.is-selected {{ background: #eef5ff; box-shadow: inset 0 0 0 2px #3f7ee8; }}
            .calendar-cell.is-muted {{
                position: relative; background: #f6f7f9; color: #8d96a6; cursor: default;
            }}
            .calendar-cell.is-muted::after {{
                content: ""; position: absolute; inset: 0;
                background: rgba(255, 255, 255, 0.48); pointer-events: none;
            }}
            .day-number {{ font-size: 0.95rem; font-weight: 700; line-height: 1; position: relative; z-index: 1; }}
            .event-stack {{ display: flex; flex-direction: column; gap: 4px; min-width: 0; position: relative; z-index: 1; }}
            .event-chip {{
                width: 100%; min-height: 22px; padding: 3px 7px; border-radius: 4px;
                overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
                box-sizing: border-box; font-size: 0.78rem; font-weight: 700; cursor: pointer;
            }}
            .event-chip:hover {{ filter: brightness(0.95); }}
            .event-chip.policy {{ background: #eef5ff; color: #245cc7; border: 1px solid #c9dcff; }}
            .event-chip.job {{ background: #fff0f0; color: #b4232c; border: 1px solid #ffd0d3; }}
            .event-chip.other {{ background: #f1f4f8; color: #4a5568; border: 1px solid #d9e0ea; }}
            .event-more {{ color: #667085; font-size: 0.76rem; font-weight: 700; }}
        </style>
        <div class="calendar-shell">
            <div class="calendar-weekdays">{weekday_headers}</div>
            <div class="calendar-grid">{''.join(cells)}</div>
        </div>
        <script>
            function selectDay(year, month, day) {{
                try {{
                    const doc = window.parent.document;
                    const input = doc.querySelector('input[aria-label="hidden_date_sync"]');
                    if (input) {{
                        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        setter.call(input, year + '-' + month + '-' + day);
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        const form = input.closest('div[data-testid="stForm"]');
                        if (form) {{
                            const submitBtn = form.querySelector('button');
                            if (submitBtn) submitBtn.click();
                        }}
                    }}
                }} catch (e) {{
                    console.error("에러 발생:", e);
                }}
            }}
        </script>
        </body>
        </html>
        """

    components.html(calendar_html, height=(len(weeks) * 116) + 44, scrolling=False)


def render_mypage():
    st.title("🗓️ My Calendar")

    if "cal_day" in st.query_params:
        try:
            st.session_state.calendar_year = int(st.query_params.get("cal_year", datetime.today().year))
            st.session_state.calendar_month = int(st.query_params.get("cal_month", datetime.today().month))
            st.session_state.selected_day = int(st.query_params["cal_day"])
            st.query_params.clear()
        except ValueError:
            pass

    # --- 달력 칸/일정 클릭 → 날짜 선택 (JS가 이 숨김 폼에 값을 넣어 제출) ---
    st.markdown(
        """
        <style>
        div[data-testid="stForm"]:has(input[aria-label="hidden_date_sync"]) {
            position: absolute; width: 0; height: 0; overflow: hidden;
            opacity: 0; border: none; padding: 0; margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.form("date_sync_form", clear_on_submit=True):
        date_sync = st.text_input("hidden_date_sync", key="hidden_date_sync", label_visibility="collapsed")
        submit_btn = st.form_submit_button("hidden_submit")

    if submit_btn and date_sync:
        try:
            y, m, d = map(int, date_sync.split("-"))
            st.session_state.calendar_year = y
            st.session_state.calendar_month = m
            st.session_state.selected_day = d
            st.rerun()
        except ValueError:
            pass

    today = datetime.today().date()

    if "calendar_year" not in st.session_state:
        st.session_state.calendar_year = today.year

    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = today.month

    if "selected_day" not in st.session_state:
        st.session_state.selected_day = today.day

    year = st.session_state.calendar_year
    month = st.session_state.calendar_month

    last_day = calendar.monthrange(year, month)[1]
    if st.session_state.selected_day > last_day:
        st.session_state.selected_day = last_day

    selected_day = st.session_state.selected_day
    events = build_events(year, month, today)

    events_by_day = {}
    for event in events:
        events_by_day.setdefault(event["day"], []).append(event)

    col_title, col_nav = st.columns([4.4, 1.35])

    with col_title:
        st.write("")

    with col_nav:
        nav_prev, nav_label, nav_next = st.columns([0.8, 1.6, 0.8])

        with nav_prev:
            if st.button("◀", key="calendar_prev"):
                move_month(-1)

        with nav_label:
            st.markdown(
                f"<div style='text-align:center; font-weight:700; white-space:nowrap; padding-top:0.45rem'>{year}. {month:02d}</div>",
                unsafe_allow_html=True,
            )

        with nav_next:
            if st.button("▶", key="calendar_next"):
                move_month(1)

    left, right = st.columns([3, 1.35])

    with left:
        render_calendar_grid(year, month, selected_day, events_by_day)
        st.caption("정책 마감 | 채용 마감 | 기타")

    with right:
        selected_date = date(year, month, selected_day)
        selected_events = events_by_day.get(selected_day, [])

        with st.container(border=True):
            st.markdown(f"### {month:02d}월 {selected_day:02d}일의 이벤트")

            if selected_events:
                for _idx, event in enumerate(selected_events):
                    meta = event_meta(event)
                    st.markdown(f"**{event['title']}**")
                    st.caption(meta['label'])
                    st.caption(f"마감: {event['date']} · {event['d_day']}")

                    c1, c2 = st.columns([2, 1])
                    with c1:
                        _lbl, _url = event_link_safe(event)
                        if _url:
                            st.link_button(_lbl, _url)
                    with c2:
                        # 중복 이벤트가 있어도 key가 겹치지 않도록 인덱스를 포함
                        if st.button(
                            "삭제",
                            key=f"delete_{_idx}_{event['source']}_{event['title']}_{event['date']}",
                        ):
                            delete_event_from_calendar(event)

                    st.divider()
            else:
                st.caption("선택한 날짜에 등록된 이벤트가 없습니다.")

        with st.container(border=True):
            st.markdown("### ➕ 일정 추가")

            category = st.selectbox(
                "분류",
                ["정책", "채용", "기타"],
                index=2,
            )
            custom_title = st.text_input(
                "일정 제목",
                placeholder="예: 포트폴리오 제출 마감",
            )
            custom_date = st.date_input(
                "일정 날짜",
                value=selected_date,
            )
            custom_link = st.text_input(
                "관련 링크",
                placeholder="https://...",
            )

            if st.button("추가하기"):
                source_by_category = {
                    "정책": "policy",
                    "채용": "job",
                    "기타": "other",
                }
                add_event_to_calendar(
                    {
                        "title": custom_title,
                        "date": custom_date.strftime("%Y-%m-%d"),
                        "source": source_by_category[category],
                        "link": custom_link,
                    }
                )

    st.divider()

    if st.button("🏠 홈으로 돌아가기"):
        st.query_params.clear()
        st.session_state.page = "home"
        st.rerun()
