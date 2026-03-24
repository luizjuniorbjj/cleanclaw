"""
CleanClaw v3 — Routes package.
All cleaning API endpoint routers.
"""

from .app_routes import router as app_router
from .onboarding import router as onboarding_router
from .clients import router as clients_router
from .services import router as services_router
from .teams import router as teams_router
from .members import router as members_router
from .schedule import router as schedule_router
from .cleaner_routes import router as cleaner_router
from .homeowner_routes import router as homeowner_router
from .invoice_routes import router as invoice_router
from .notification_routes import router as notification_router
from .dashboard_routes import router as dashboard_router
from .settings_routes import router as settings_router
from .ai_routes import router as ai_router
from .auth_routes import router as auth_router
from .plan import router as plan_router

__all__ = [
    "app_router",
    "onboarding_router",
    "clients_router",
    "services_router",
    "teams_router",
    "members_router",
    "schedule_router",
    "cleaner_router",
    "homeowner_router",
    "invoice_router",
    "notification_router",
    "dashboard_router",
    "settings_router",
    "ai_router",
    "auth_router",
    "plan_router",
]
