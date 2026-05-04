from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
TOPICS_PATH = ROOT_DIR / "data" / "topics.json"


@dataclass(frozen=True)
class AppConfig:
    storage_mode: str
    supabase_url: str | None
    supabase_key: str | None
    supabase_bucket: str
    admin_password: str | None
    max_upload_mb: int

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_key and self.supabase_bucket)

    @property
    def effective_storage_mode(self) -> str:
        if self.storage_mode == "supabase" and self.supabase_configured:
            return "supabase"
        return "local_demo"


def _secret(path: str, default: Any = None) -> Any:
    try:
        current: Any = st.secrets
        for key in path.split("."):
            if hasattr(current, "get"):
                current = current.get(key, default)
            else:
                current = current[key]
            if current is default:
                return default
        return current
    except Exception:
        return default


@st.cache_data(show_spinner=False)
def load_topics() -> list[dict]:
    if not TOPICS_PATH.exists():
        return []
    with TOPICS_PATH.open("r", encoding="utf-8") as file:
        topics = json.load(file)
    return topics if isinstance(topics, list) else []


def get_topic_by_id(lesson_id: str) -> dict | None:
    return next((topic for topic in load_topics() if topic.get("id") == lesson_id), None)


def get_app_config() -> AppConfig:
    storage_mode = str(_secret("app.storage_mode", "supabase")).strip().lower()
    if storage_mode not in {"supabase", "local_demo"}:
        storage_mode = "supabase"

    return AppConfig(
        storage_mode=storage_mode,
        supabase_url=_secret("supabase.url"),
        supabase_key=_secret("supabase.service_role_key") or _secret("supabase.anon_key"),
        supabase_bucket=str(_secret("supabase.storage_bucket", "class-photos")),
        admin_password=_secret("admin.password"),
        max_upload_mb=int(_secret("app.max_upload_mb", 5)),
    )
