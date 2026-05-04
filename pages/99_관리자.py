from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from utils.auth import require_admin
from utils.config import get_app_config, load_topics
from utils.storage import StorageError, fetch_submissions
from utils.ui import apply_global_styles, render_header, render_storage_notice


def _prepare_dataframe(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        df["date"] = df["created_at"].dt.date
    if "numeric_value" in df.columns:
        df["numeric_value"] = pd.to_numeric(df["numeric_value"], errors="coerce")
    return df


def _filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    topics = ["전체"] + sorted(df["lesson_title"].dropna().astype(str).unique().tolist())
    classes = ["전체"] + sorted(df["class_name"].fillna("").astype(str).replace("", "미입력").unique().tolist())
    groups = ["전체"] + sorted(df["group_name"].fillna("").astype(str).replace("", "미입력").unique().tolist())

    filter_cols = st.columns(4)
    with filter_cols[0]:
        lesson_filter = st.selectbox("수업 주제", topics)
    with filter_cols[1]:
        class_filter = st.selectbox("반", classes)
    with filter_cols[2]:
        group_filter = st.selectbox("모둠", groups)
    with filter_cols[3]:
        if "date" in df.columns and df["date"].notna().any():
            min_date = df["date"].dropna().min()
            max_date = df["date"].dropna().max()
        else:
            min_date = max_date = date.today()
        date_range = st.date_input("날짜", value=(min_date, max_date))

    filtered = df.copy()
    if lesson_filter != "전체":
        filtered = filtered[filtered["lesson_title"].astype(str) == lesson_filter]
    if class_filter != "전체":
        class_series = filtered["class_name"].fillna("").astype(str).replace("", "미입력")
        filtered = filtered[class_series == class_filter]
    if group_filter != "전체":
        group_series = filtered["group_name"].fillna("").astype(str).replace("", "미입력")
        filtered = filtered[group_series == group_filter]
    if isinstance(date_range, tuple) and len(date_range) == 2 and "date" in filtered.columns:
        start_date, end_date = date_range
        filtered = filtered[(filtered["date"] >= start_date) & (filtered["date"] <= end_date)]
    return filtered


def _show_stats(df: pd.DataFrame) -> None:
    numeric = df["numeric_value"].dropna() if "numeric_value" in df.columns else pd.Series(dtype=float)
    metric_cols = st.columns(4)
    metric_cols[0].metric("제출 수", f"{len(df):,}")
    metric_cols[1].metric("평균", "-" if numeric.empty else f"{numeric.mean():.2f}")
    metric_cols[2].metric("최솟값", "-" if numeric.empty else f"{numeric.min():.2f}")
    metric_cols[3].metric("최댓값", "-" if numeric.empty else f"{numeric.max():.2f}")


def main() -> None:
    st.set_page_config(
        page_title="관리자 페이지",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_global_styles()

    config = get_app_config()
    render_header(
        eyebrow="Teacher Admin",
        title="수업 제출 데이터 확인",
        description="공개수업 중 학생 제출 자료를 필터링하고 CSV로 내려받습니다.",
    )
    render_storage_notice(config)

    if not require_admin(config):
        st.stop()

    topics = load_topics()
    st.caption(f"등록된 수업 주제 {len(topics)}개")

    try:
        rows = fetch_submissions(config)
    except StorageError as exc:
        st.error(f"데이터를 불러오지 못했습니다: {exc}")
        st.stop()

    df = _prepare_dataframe(rows)
    if df.empty:
        st.info("아직 제출 데이터가 없습니다.")
        st.stop()

    st.markdown('<div class="section-title">필터</div>', unsafe_allow_html=True)
    filtered = _filter_dataframe(df)

    st.markdown('<div class="section-title">기초 통계</div>', unsafe_allow_html=True)
    _show_stats(filtered)

    st.markdown('<div class="section-title">제출 데이터</div>', unsafe_allow_html=True)
    display_columns = [
        "created_at",
        "lesson_title",
        "student_code",
        "class_name",
        "group_name",
        "numeric_value",
        "text_response",
        "image_url",
        "image_path",
        "device_hint",
    ]
    display_df = filtered[[col for col in display_columns if col in filtered.columns]].copy()
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "image_url": st.column_config.ImageColumn("사진"),
            "image_path": st.column_config.TextColumn("사진 경로"),
            "text_response": st.column_config.TextColumn("설명", width="large"),
        },
    )

    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "필터 결과 CSV 다운로드",
        data=csv,
        file_name="class_submissions.csv",
        mime="text/csv",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
