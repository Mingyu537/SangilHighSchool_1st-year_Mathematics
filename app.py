from __future__ import annotations

import streamlit as st

from utils.config import get_app_config, load_topics
from utils.ui import (
    apply_global_styles,
    lesson_card,
    render_header,
    render_storage_notice,
    status_pill,
)


def main() -> None:
    st.set_page_config(
        page_title="공개수업 활동 앱",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_global_styles()

    config = get_app_config()
    topics = load_topics()
    active_topics = [topic for topic in topics if topic.get("active", True)]

    render_header(
        eyebrow="Sangil Mathematics Class",
        title="수업 중 생각과 자료를 바로 모으는 활동 앱",
        description=(
            "학생은 익명 코드로 숫자, 설명, 사진을 제출하고 교사는 관리자 페이지에서 "
            "수업 결과를 바로 확인할 수 있습니다."
        ),
    )
    render_storage_notice(config)

    if active_topics:
        if "selected_lesson_id" not in st.session_state:
            st.session_state.selected_lesson_id = active_topics[0]["id"]

        topic_labels = {f"{topic['title']}": topic["id"] for topic in active_topics}
        current_title = next(
            (topic["title"] for topic in active_topics if topic["id"] == st.session_state.selected_lesson_id),
            active_topics[0]["title"],
        )
        selected_title = st.selectbox(
            "현재 수업 주제",
            options=list(topic_labels.keys()),
            index=list(topic_labels.keys()).index(current_title)
            if current_title in topic_labels
            else 0,
        )
        st.session_state.selected_lesson_id = topic_labels[selected_title]

    st.markdown('<div class="section-title">오늘 사용할 수업 주제</div>', unsafe_allow_html=True)
    if not active_topics:
        st.warning("data/topics.json에 활성화된 수업 주제가 없습니다.")
    else:
        for topic in active_topics:
            lesson_card(topic, selected=topic["id"] == st.session_state.selected_lesson_id)

    action_left, action_right = st.columns([1, 1])
    with action_left:
        st.page_link(
            "pages/01_수업활동.py",
            label="학생용 활동 시작",
            icon="✍️",
            use_container_width=True,
        )
    with action_right:
        st.page_link(
            "pages/99_관리자.py",
            label="관리자 페이지",
            icon="🔒",
            use_container_width=True,
        )

    st.markdown('<div class="section-title">운영 원칙</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        status_pill("익명 중심", "학생 실명 대신 닉네임 또는 익명 코드를 사용합니다.")
    with col2:
        status_pill("Supabase 저장", "배포 환경에서는 Database와 Storage에 제출 데이터를 저장합니다.")
    with col3:
        status_pill("확장 가능", "topics.json에 주제를 추가해 다른 수업 활동으로 확장합니다.")


if __name__ == "__main__":
    main()
