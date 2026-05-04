from __future__ import annotations

import hmac

import streamlit as st

from utils.config import AppConfig


def require_admin(config: AppConfig) -> bool:
    if st.session_state.get("admin_authenticated"):
        return True

    st.markdown('<div class="section-title">관리자 인증</div>', unsafe_allow_html=True)
    if not config.admin_password:
        st.error("관리자 비밀번호가 설정되어 있지 않습니다. Streamlit secrets에 admin.password를 추가하세요.")
        return False

    with st.form("admin_login_form"):
        password = st.text_input("관리자 비밀번호", type="password")
        submitted = st.form_submit_button("관리자 페이지 열기", type="primary", use_container_width=True)

    if not submitted:
        return False

    if hmac.compare_digest(password, config.admin_password):
        st.session_state.admin_authenticated = True
        st.rerun()

    st.error("비밀번호가 올바르지 않습니다.")
    return False
