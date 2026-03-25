"""
Xcleaners v3 — Frontend App Routes.

Serves the Xcleaners PWA shell and static assets.

Routes:
  GET  /cleaning/app            — serves app.html (PWA entry point)
  GET  /cleaning/app/{path}     — SPA catch-all (serves app.html)
  GET  /cleaning/manifest.json  — PWA manifest
  GET  /cleaning/sw.js          — Service Worker
  Static files:
  GET  /cleaning/static/*       — CSS, JS, icons
"""

import logging
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

logger = logging.getLogger("xcleaners.app_routes")

router = APIRouter(tags=["Xcleaners Frontend"], include_in_schema=False)

# Resolve frontend/cleaning directory relative to project root
_cleaning_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "frontend" / "cleaning"


@router.get("/cleaning/app")
async def serve_cleaning_app():
    """Serve the Xcleaners PWA shell."""
    return FileResponse(
        str(_cleaning_dir / "app.html"),
        media_type="text/html",
    )


@router.get("/cleaning/app/{path:path}")
async def serve_cleaning_app_catchall(path: str):
    """SPA catch-all — all /cleaning/app/* routes serve app.html."""
    return FileResponse(
        str(_cleaning_dir / "app.html"),
        media_type="text/html",
    )


@router.get("/cleaning/manifest.json")
async def serve_manifest():
    """Serve PWA manifest."""
    return FileResponse(
        str(_cleaning_dir / "manifest.json"),
        media_type="application/json",
    )


@router.get("/cleaning/sw.js")
async def serve_service_worker():
    """Serve service worker with correct scope headers."""
    return FileResponse(
        str(_cleaning_dir / "sw.js"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/cleaning/"},
    )
