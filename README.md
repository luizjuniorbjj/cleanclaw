# CleanClaw

Smart Cleaning Business Management PWA

## Quick Start
1. Copy `.env.example` to `.env` and fill in values
2. `pip install -r requirements.txt`
3. `python cleanclaw_main.py`
4. Open http://localhost:8003/cleaning/app

## Demo Accounts
| Email | Password | Role |
|-------|----------|------|
| superadmin@cleanclaw.com | admin123 | Super Admin |
| admin@cleanclaw.com | admin123 | Owner |
| cleaner@cleanclaw.com | admin123 | Cleaner |
| donocasa@cleanclaw.com | admin123 | Homeowner |

## Tech Stack
- Backend: Python 3.12 + FastAPI
- Frontend: HTML/CSS/JS (PWA)
- Database: PostgreSQL 16
- Cache: Redis 7
- Deploy: Railway (Docker)
