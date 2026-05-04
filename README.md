# 공개수업 수학 활동 Streamlit 앱

중학생 또는 고등학생이 수업 중 익명 코드로 숫자 데이터, 설명, 사진을 제출하고, 교사가 관리자 페이지에서 제출 결과를 바로 확인하는 수업용 웹앱입니다.

앱은 처음에는 하나의 수업 주제로 시작하지만, `data/topics.json`에 항목을 추가해 다른 수업 주제와 활동으로 확장할 수 있도록 구성되어 있습니다.

## 주요 기능

- 학생용 활동 화면: 익명 코드, 반, 모둠, 숫자 데이터, 설명, 사진 제출
- 관리자 화면: 비밀번호 인증, 제출 데이터 조회, 날짜/수업 주제/반/모둠 필터, 기초 통계, CSV 다운로드
- Supabase 저장: 제출 데이터는 Database, 사진은 Storage에 저장
- local_demo 모드: Supabase가 없는 개발 환경에서 세션 기반으로 제출 흐름 확인
- 모바일 우선 반응형 UI: 스마트폰, 태블릿, 데스크톱 대응

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

기존 Streamlit 템플릿 호환을 위해 `streamlit_app.py`도 `app.py`를 실행하도록 유지되어 있습니다.

## Streamlit Community Cloud 배포

1. GitHub 저장소를 Streamlit Community Cloud에 연결합니다.
2. Main file path를 `app.py`로 설정합니다.
3. App settings의 Secrets에 `.streamlit/secrets.example.toml` 형식을 참고해 값을 입력합니다.
4. 배포 후 학생에게 앱 URL을 공유합니다.

## 필요한 Secrets

실제 `.streamlit/secrets.toml`은 Git에 올리지 않습니다. 로컬에서는 `.streamlit/secrets.example.toml`을 복사해 값을 채우세요.

```toml
[app]
storage_mode = "supabase"
max_upload_mb = 5

[admin]
password = "replace-with-a-strong-admin-password"

[supabase]
url = "https://your-project-ref.supabase.co"
service_role_key = "your-service-role-key"
storage_bucket = "class-photos"
```

Supabase 설정이 없으면 앱은 죽지 않고 `local_demo` 모드로 실행됩니다. 단, 이 모드는 현재 Streamlit 세션에서만 유지되며 프로덕션 저장소가 아닙니다.

## Supabase 설정

### 1. Database 테이블

Supabase SQL Editor에서 아래 SQL을 실행합니다.

```sql
create table if not exists submissions (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  lesson_id text not null,
  lesson_title text not null,
  student_code text not null,
  class_name text,
  group_name text,
  numeric_value double precision,
  text_response text,
  image_path text,
  image_url text,
  device_hint text,
  user_agent_optional text
);

create index if not exists idx_submissions_created_at
  on submissions (created_at desc);

create index if not exists idx_submissions_lesson_class_group
  on submissions (lesson_id, class_name, group_name);
```

### 2. Storage 버킷

Supabase Storage에서 `class-photos` 버킷을 생성합니다.

사진 경로는 다음 형식으로 저장됩니다.

```text
lesson_id/date/student_code/uuid_filename
```

예시:

```text
rate-of-change-open-class/2026-05-05/A12/9f0c...e3.jpg
```

버킷을 public으로 만들면 관리자 페이지에서 이미지 썸네일이 바로 보입니다. private으로 운영하려면 `image_path`를 기준으로 별도 signed URL 발급 로직을 추가하세요.

## 관리자 페이지 접속

앱 홈에서 `관리자 페이지` 버튼을 누르거나 Streamlit 사이드바에서 `99_관리자` 페이지로 이동합니다.

관리자 비밀번호는 반드시 Streamlit secrets의 `admin.password`에서 불러옵니다. 코드에 하드코딩하지 않습니다.

## 수업 주제 추가

`data/topics.json`에 새 객체를 추가합니다.

```json
{
  "id": "new-lesson-id",
  "active": true,
  "grade_band": "고등 수학",
  "title": "새 수업 주제",
  "description": "수업 활동 설명",
  "key_question": "핵심 질문",
  "numeric_label": "숫자 입력 라벨",
  "numeric_help": "숫자 입력 도움말",
  "text_prompt": "텍스트 입력 질문",
  "image_prompt": "사진 업로드 안내",
  "class_options": ["1반", "2반"],
  "group_options": ["1모둠", "2모둠"],
  "activity_steps": ["활동 단계 1", "활동 단계 2"]
}
```

페이지 코드를 복사하지 않고 JSON만 확장하는 방식을 우선합니다.

## 데이터 저장 구조

`submissions` 테이블 기준 필드는 다음과 같습니다.

- `id`
- `created_at`
- `lesson_id`
- `lesson_title`
- `student_code`
- `class_name`
- `group_name`
- `numeric_value`
- `text_response`
- `image_path`
- `image_url`
- `device_hint`
- `user_agent_optional`

학생 실명은 요구하지 않으며, `student_code` 또는 닉네임 중심으로 저장합니다.
