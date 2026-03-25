# Xcleaners

Smart Cleaning Business Management PWA

## Quick Start
1. `cp .env.example .env` and fill in values
2. `pip install -r requirements.txt`
3. `python xcleaners_main.py`
4. Open http://localhost:8003/cleaning/app

## Dev Setup (with test dependencies)
```bash
pip install -r requirements-dev.txt
```

## Demo Accounts
| Email | Password | Role |
|-------|----------|------|
| superadmin@xcleaners.app | admin123 | Super Admin |
| admin@xcleaners.app | admin123 | Owner |
| cleaner@xcleaners.app | admin123 | Cleaner |
| donocasa@xcleaners.app | admin123 | Homeowner |

## Tech Stack
- Backend: Python 3.12 + FastAPI
- Frontend: HTML/CSS/JS (PWA)
- Database: PostgreSQL 16
- Cache: Redis 7
- Deploy: Railway (Docker)
