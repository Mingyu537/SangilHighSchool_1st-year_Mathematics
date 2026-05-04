from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from PIL import Image, UnidentifiedImageError

from utils.config import get_app_config, get_topic_by_id, load_topics
from utils.storage import StorageError, save_submission
from utils.ui import (
    apply_global_styles,
    field_summary,
    render_header,
    render_storage_notice,
)


MAX_TEXT_LENGTH = 800


def _current_topic() -> dict:
    topics = load_topics()
    selected_lesson_id = st.session_state.get("selected_lesson_id")
    if selected_lesson_id:
        topic = get_topic_by_id(selected_lesson_id)
        if topic:
            return topic
    return topics[0]


def _validate_image(uploaded_file, max_upload_mb: int) -> tuple[bytes | None, str | None]:
    if uploaded_file is None:
        return None, None

    image_bytes = uploaded_file.getvalue()
    max_bytes = max_upload_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        return None, f"사진 파일은 {max_upload_mb}MB 이하로 업로드해 주세요."

    try:
        Image.open(uploaded_file).verify()
    except (UnidentifiedImageError, OSError):
        return None, "이미지 파일을 확인할 수 없습니다. png, jpg, jpeg 파일만 업로드해 주세요."
    finally:
        uploaded_file.seek(0)

    return image_bytes, None


def main() -> None:
    st.set_page_config(
        page_title="학생 수업 활동",
        page_icon="✍️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_global_styles()

    config = get_app_config()
    topic = _current_topic()
    submission_key = f"submitted_{topic['id']}"

    render_header(
        eyebrow="Student Activity",
        title=topic["title"],
        description=topic["key_question"],
    )
    render_storage_notice(config)

    if st.session_state.get(submission_key):
        st.success("제출이 완료되었습니다. 같은 기기에서는 중복 제출을 막기 위해 제출 버튼을 잠가두었습니다.")
        if st.button("새 응답 작성하기", type="secondary"):
            st.session_state[submission_key] = False
            st.rerun()
        st.stop()

    st.markdown('<div class="section-title">활동 안내</div>', unsafe_allow_html=True)
    for step in topic.get("activity_steps", []):
        st.markdown(f"- {step}")

    with st.form("student_submission_form", clear_on_submit=False):
        st.markdown('<div class="section-title">내 응답 입력</div>', unsafe_allow_html=True)
        student_code = st.text_input(
            "익명 코드 또는 닉네임",
            max_chars=40,
            placeholder="예: A12, 별빛수학, 2모둠-3",
            help="실명 대신 본인이 알아볼 수 있는 익명 코드를 입력합니다.",
        )

        meta_cols = st.columns(3)
        with meta_cols[0]:
            class_name = st.selectbox(
                "반 선택",
                options=["선택 안 함"] + topic.get("class_options", []),
            )
        with meta_cols[1]:
            group_name = st.selectbox(
                "모둠 선택",
                options=["선택 안 함"] + topic.get("group_options", []),
            )
        with meta_cols[2]:
            device_hint = st.selectbox(
                "접속 기기",
                options=["스마트폰", "태블릿", "컴퓨터", "기타"],
            )

        numeric_value = st.number_input(
            topic.get("numeric_label", "숫자 데이터"),
            value=None,
            placeholder="숫자를 입력하세요",
            help=topic.get("numeric_help", ""),
        )
        text_response = st.text_area(
            topic.get("text_prompt", "생각을 적어 주세요."),
            max_chars=MAX_TEXT_LENGTH,
            height=150,
            placeholder="관찰한 점, 이유, 질문 등을 짧게 적어 주세요.",
        )
        uploaded_file = st.file_uploader(
            topic.get("image_prompt", "사진을 업로드하세요."),
            type=["png", "jpg", "jpeg"],
            help=f"png, jpg, jpeg만 가능하며 {config.max_upload_mb}MB 이하 파일을 권장합니다.",
        )
        confirmed = st.checkbox("제출 전 입력 내용을 확인했습니다.")
        submitted = st.form_submit_button("응답 제출", type="primary", use_container_width=True)

    image_bytes, image_error = _validate_image(uploaded_file, config.max_upload_mb)
    if image_error:
        st.error(image_error)

    st.markdown('<div class="section-title">제출 전 확인</div>', unsafe_allow_html=True)
    field_summary(
        {
            "수업 주제": topic["title"],
            "익명 코드": student_code or "미입력",
            "반": "" if class_name == "선택 안 함" else class_name,
            "모둠": "" if group_name == "선택 안 함" else group_name,
            "숫자 데이터": numeric_value,
            "설명": text_response or "미입력",
            "사진": uploaded_file.name if uploaded_file else "없음",
        }
    )

    if submitted:
        if not student_code.strip():
            st.error("익명 코드 또는 닉네임을 입력해 주세요.")
            st.stop()
        if numeric_value is None:
            st.error("숫자 데이터를 입력해 주세요.")
            st.stop()
        if not text_response.strip():
            st.error("짧은 설명 또는 생각을 입력해 주세요.")
            st.stop()
        if image_error:
            st.stop()
        if not confirmed:
            st.error("제출 전 확인 체크박스를 선택해 주세요.")
            st.stop()

        payload = {
            "lesson_id": topic["id"],
            "lesson_title": topic["title"],
            "student_code": student_code.strip(),
            "class_name": "" if class_name == "선택 안 함" else class_name,
            "group_name": "" if group_name == "선택 안 함" else group_name,
            "numeric_value": float(numeric_value),
            "text_response": text_response.strip(),
            "device_hint": device_hint,
            "user_agent_optional": None,
            "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
        }

        try:
            save_submission(
                payload=payload,
                image_bytes=image_bytes,
                image_name=uploaded_file.name if uploaded_file else None,
                image_mime=uploaded_file.type if uploaded_file else None,
                config=config,
            )
        except StorageError as exc:
            st.error(f"저장 중 문제가 발생했습니다: {exc}")
            st.stop()

        st.session_state[submission_key] = True
        st.success("응답이 저장되었습니다. 참여해 주셔서 감사합니다.")
        st.balloons()


if __name__ == "__main__":
    main()
