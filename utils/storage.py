from __future__ import annotations

import base64
import mimetypes
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from supabase import Client, create_client

from utils.config import AppConfig


class StorageError(RuntimeError):
    pass


def _get_client(config: AppConfig) -> Client:
    if not config.supabase_configured:
        raise StorageError("Supabase URL, key, storage bucket 설정이 필요합니다.")
    return create_client(config.supabase_url, config.supabase_key)


def _safe_segment(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z가-힣_-]+", "-", value.strip())
    return cleaned.strip("-")[:60] or "anonymous"


def _image_path(lesson_id: str, student_code: str, image_name: str) -> str:
    suffix = Path(image_name).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg"}:
        suffix = mimetypes.guess_extension(mimetypes.guess_type(image_name)[0] or "") or ".jpg"
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"{uuid.uuid4().hex}{suffix}"
    return f"{_safe_segment(lesson_id)}/{today}/{_safe_segment(student_code)}/{filename}"


def _local_demo_rows() -> list[dict[str, Any]]:
    return st.session_state.setdefault("local_demo_submissions", [])


def _save_local_demo(
    payload: dict[str, Any],
    image_bytes: bytes | None,
    image_name: str | None,
    image_mime: str | None,
) -> dict[str, Any]:
    row = {
        "id": str(uuid.uuid4()),
        **payload,
        "image_path": None,
        "image_url": None,
    }
    if image_bytes and image_name:
        mime = image_mime or "image/jpeg"
        row["image_path"] = f"local_demo/{image_name}"
        row["image_url"] = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"

    _local_demo_rows().append(row)
    return row


def save_submission(
    payload: dict[str, Any],
    image_bytes: bytes | None,
    image_name: str | None,
    image_mime: str | None,
    config: AppConfig,
) -> dict[str, Any]:
    if config.effective_storage_mode == "local_demo":
        return _save_local_demo(payload, image_bytes, image_name, image_mime)

    client = _get_client(config)
    row = {**payload, "image_path": None, "image_url": None}

    if image_bytes and image_name:
        path = _image_path(payload["lesson_id"], payload["student_code"], image_name)
        try:
            client.storage.from_(config.supabase_bucket).upload(
                path,
                image_bytes,
                file_options={
                    "content-type": image_mime or "image/jpeg",
                    "upsert": "false",
                },
            )
        except Exception as exc:
            raise StorageError(f"사진 업로드 실패: {exc}") from exc

        row["image_path"] = path
        try:
            row["image_url"] = client.storage.from_(config.supabase_bucket).get_public_url(path)
        except Exception:
            row["image_url"] = None

    try:
        response = client.table("submissions").insert(row).execute()
    except Exception as exc:
        raise StorageError(f"제출 데이터 저장 실패: {exc}") from exc

    data = getattr(response, "data", None)
    return data[0] if data else row


def fetch_submissions(config: AppConfig) -> list[dict[str, Any]]:
    if config.effective_storage_mode == "local_demo":
        return list(reversed(_local_demo_rows()))

    client = _get_client(config)
    try:
        response = client.table("submissions").select("*").order("created_at", desc=True).execute()
    except Exception as exc:
        raise StorageError(f"Supabase 조회 실패: {exc}") from exc

    return getattr(response, "data", []) or []
