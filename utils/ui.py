from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import streamlit as st

from utils.config import AppConfig


ROOT_DIR = Path(__file__).resolve().parents[1]
STYLE_PATH = ROOT_DIR / "assets" / "style.css"


def apply_global_styles() -> None:
    if STYLE_PATH.exists():
        st.markdown(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_header(eyebrow: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="orb orb-one"></div>
            <div class="orb orb-two"></div>
            <div class="hero-content">
                <p class="hero-eyebrow">{html.escape(eyebrow)}</p>
                <h1>{html.escape(title)}</h1>
                <p>{html.escape(description)}</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_storage_notice(config: AppConfig) -> None:
    if config.effective_storage_mode == "supabase":
        st.success("Supabase 저장소가 연결되어 있습니다.")
        return

    if config.storage_mode == "supabase":
        st.warning(
            "Supabase secrets가 없어 local_demo 모드로 실행 중입니다. "
            "local_demo 데이터는 현재 Streamlit 세션에서만 유지되며 프로덕션 저장소가 아닙니다."
        )
    else:
        st.info("local_demo 모드입니다. 개발 확인용이며 실제 수업 배포 저장소로 사용하지 마세요.")


def lesson_card(topic: dict, selected: bool = False) -> None:
    selected_class = " selected" if selected else ""
    st.markdown(
        f"""
        <article class="neo-card lesson-card{selected_class}">
            <div>
                <span class="chip">{html.escape(topic.get("grade_band", "수업 활동"))}</span>
                <h3>{html.escape(topic.get("title", "수업 주제"))}</h3>
                <p>{html.escape(topic.get("description", ""))}</p>
            </div>
            <div class="question-box">{html.escape(topic.get("key_question", ""))}</div>
        </article>
        """,
        unsafe_allow_html=True,
    )


def status_pill(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="neo-card mini-card">
            <strong>{html.escape(title)}</strong>
            <span>{html.escape(body)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def field_summary(items: dict[str, Any]) -> None:
    rows = []
    for key, value in items.items():
        rows.append(
            f"""
            <div class="summary-row">
                <span>{html.escape(str(key))}</span>
                <strong>{html.escape("" if value is None else str(value))}</strong>
            </div>
            """
        )
    st.markdown(
        f'<div class="neo-card summary-card">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )
