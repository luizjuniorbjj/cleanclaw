# Xcleaners — CLAUDE.md

## Stack
- Backend: Python 3.12 + FastAPI
- Frontend: HTML/CSS/JS puro (PWA)
- Database: PostgreSQL 16
- Cache: Redis 7
- Deploy: Railway (Docker)

## Entry Point
- `xcleaners_main.py` — standalone FastAPI on port 8003

## Structure
app/modules/cleaning/ — all backend code
frontend/cleaning/ — all frontend code
database/migrations/ — SQL migrations (011-019)

## Roles
- super_admin: platform management
- owner: business management
- cleaner: job execution
- homeowner: booking and payment

## Demo Mode
Demo accounts bypass auth when DB unavailable.
DemoData provides mock data for all screens.
