# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

课堂学情监控管理系统 — Students send emoji reactions (scored 1–6) during class, teachers view real-time aggregated statistics (count, distribution, average, variance, bar/pie charts). Includes discussion forum for real-time text/image exchange and admin user management.

## Tech Stack

- **Backend**: Django 4.2 + DRF + Django Channels (WebSocket) + SQLite (dev) / MySQL (prod)
- **Frontend**: Vue 3 + Vite + Element Plus + ECharts + Pinia + Axios
- **Auth**: JWT (djangorestframework-simplejwt)

## Development Commands

```bash
# Backend
cd backend
source venv/bin/activate
python manage.py runserver              # HTTP on :8000
daphne -b 0.0.0.0 -p 8000 config.asgi:application  # HTTP + WebSocket

# Frontend
cd frontend
npm run dev                             # Vite dev server on :5173 (proxies /api, /ws to :8000)
npm run build                           # Production build to dist/

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser        # then set user.role='admin' via shell
```

## Architecture

```
backend/
  config/          — Django project settings, URLs, ASGI, WebSocket routing
  apps/
    users/         — User model (AbstractUser + role), StudentProfile, TeacherProfile, JWT login, admin CRUD API
    feedback/      — Course, ClassSession, EmojiReaction models; submit/statistics/history/export APIs; FeedbackConsumer (WebSocket)
    discussion/    — Message model; send/list APIs; ChatConsumer (WebSocket)

frontend/src/
  api/             — Axios instance with JWT interceptor
  stores/          — Pinia user store (auth state)
  utils/           — WebSocket helper with auto-reconnect
  router/          — Vue Router with role-based guards
  views/
    Login.vue      — Password login
    student/       — Dashboard (emoji selection), Discussion (chat)
    teacher/       — Dashboard (course/session mgmt), Statistics (ECharts), History (query+export), Discussion
    admin/         — UserManagement (CRUD table with search/filter)
```

## Key API Endpoints

- `POST /api/auth/login/` — returns JWT + user info
- `GET /api/auth/me/` — current user
- `/api/auth/users/` — admin CRUD (GET list, POST create, PATCH update, DELETE)
- `POST /api/feedback/submit/` — student submits emoji reaction
- `GET /api/feedback/statistics/<session_id>/` — current stats
- `GET /api/feedback/statistics/<session_id>/slots/` — all time slots
- `GET /api/feedback/history/` — historical query
- `GET /api/feedback/export/<session_id>/` — Excel download
- `ws/feedback/<session_id>/` — real-time statistics push
- `ws/chat/<session_id>/` — real-time chat

## Default Accounts

- Admin: username=`admin`, password=`REDACTED_ADMIN_PASSWORD`

## Notes

- Vite proxy handles `/api` and `/ws` forwarding to Django in dev mode
- WebSocket requires ASGI server (daphne); `runserver` works for HTTP-only dev
- Channel layer uses InMemoryChannelLayer (dev); switch to Redis for production
- SMS and third-party (WeChat/QQ) auth are not yet implemented (interfaces reserved)
