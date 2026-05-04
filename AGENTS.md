# AGENTS.md

This project is a classroom Streamlit web app for public lesson activities.

## Project Principles

- The app is mobile-first. Student screens must work naturally on smartphones and tablets before desktop polish is considered complete.
- Streamlit Community Cloud deployment is assumed.
- Do not treat local files as production storage. Streamlit Community Cloud local disk persistence is not guaranteed.
- Production submissions use Supabase Database for text, numeric, choice, and metadata fields.
- Production image uploads use Supabase Storage, with the uploaded path or URL saved in the `submissions` table.
- `local_demo` mode is only for development checks. It must not be presented as durable storage.
- Minimize student personal information. Ask for an anonymous code or nickname, not a real name.
- Secrets such as admin passwords, Supabase URL, and API keys must come from Streamlit secrets.
- When adding new features, preserve the topic expansion model based on `data/topics.json`.

## Structure

- `app.py`: home screen and topic overview
- `pages/01_수업활동.py`: student submission flow
- `pages/99_관리자.py`: teacher admin dashboard
- `utils/storage.py`: Supabase and local demo storage logic
- `utils/auth.py`: admin authentication
- `utils/ui.py`: CSS loading and repeated UI blocks
- `utils/config.py`: topics and Streamlit secrets configuration
- `assets/style.css`: mobile-first Neo 3D and dynamic gradient styling
- `data/topics.json`: lesson topic definitions

## Editing Guidance

- Keep `app.py` small. Put reusable logic in `utils`.
- Do not hardcode secrets or production credentials.
- Keep upload file types limited to png, jpg, and jpeg unless the teacher explicitly changes the policy.
- Add new lessons by editing `data/topics.json` rather than duplicating page code.
- Preserve clear error states for missing Supabase secrets and failed storage operations.
