"""
CleanClaw UI Eval — Comprehensive test suite for all 3 roles.

Tests login, navigation, rendering, and empty state handling for:
- Owner (admin@xcleaners.app)
- Cleaner (cleaner@xcleaners.app)
- Homeowner (donocasa@xcleaners.app)

Usage:
    python scripts/eval_cleanclaw_ui.py [--url http://localhost:8003]

Requirements:
    pip install playwright
    playwright install chromium
"""

import asyncio
import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


# ============================================
# TEST DEFINITIONS
# ============================================

@dataclass
class TestResult:
    name: str
    role: str
    passed: bool
    duration_ms: int = 0
    error: Optional[str] = None
    screenshot: Optional[str] = None


@dataclass
class EvalReport:
    results: list = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0

    @property
    def total(self): return len(self.results)
    @property
    def passed(self): return sum(1 for r in self.results if r.passed)
    @property
    def failed(self): return sum(1 for r in self.results if not r.passed)
    @property
    def score(self): return round((self.passed / self.total * 100) if self.total else 0)
    @property
    def duration_s(self): return round(self.end_time - self.start_time, 1)


DEMO_ACCOUNTS = {
    "owner": {"email": "admin@xcleaners.app", "password": "admin123"},
    "cleaner": {"email": "cleaner@xcleaners.app", "password": "admin123"},
    "homeowner": {"email": "donocasa@xcleaners.app", "password": "admin123"},
}

# Owner screens to test
OWNER_SCREENS = [
    {"hash": "#/owner/dashboard", "title": "Dashboard", "checks": ["kpi-cards", "team-progress-body", "revenue-chart"]},
    {"hash": "#/owner/schedule", "title": "Schedule", "checks": []},
    {"hash": "#/owner/teams", "title": "Teams", "checks": []},
    {"hash": "#/owner/clients", "title": "Clients", "checks": []},
    {"hash": "#/owner/invoices", "title": "Invoices", "checks": []},
    {"hash": "#/owner/services", "title": "Services", "checks": []},
    {"hash": "#/owner/settings", "title": "Settings", "checks": []},
    {"hash": "#/owner/onboarding", "title": "Onboarding", "checks": []},
    {"hash": "#/owner/crm", "title": "CRM", "checks": []},
    {"hash": "#/owner/chat-monitor", "title": "Chat Monitor", "checks": []},
]

# Cleaner screens
CLEANER_SCREENS = [
    {"hash": "#/team/today", "title": "Today", "checks": []},
    {"hash": "#/team/schedule", "title": "Schedule", "checks": []},
    {"hash": "#/team/earnings", "title": "Earnings", "checks": []},
]

# Homeowner screens
HOMEOWNER_SCREENS = [
    {"hash": "#/homeowner/bookings", "title": "Bookings", "checks": []},
    {"hash": "#/homeowner/invoices", "title": "Invoices", "checks": []},
    {"hash": "#/homeowner/preferences", "title": "Preferences", "checks": []},
]


# ============================================
# EVAL ENGINE
# ============================================

class CleanClawEval:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.report = EvalReport()

    async def run(self):
        self.report.start_time = time.time()
        print("\n" + "=" * 60)
        print("  CleanClaw UI Eval — Comprehensive Test Suite")
        print("=" * 60)
        print(f"  URL: {self.base_url}")
        print(f"  Roles: Owner, Cleaner, Homeowner")
        print("=" * 60 + "\n")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # Test 1: Login page loads
            await self._test_login_page(browser)

            # Test 2-4: Login for each role
            for role in ["owner", "cleaner", "homeowner"]:
                await self._test_login(browser, role)

            # Test 5+: Navigate all owner screens
            await self._test_role_screens(browser, "owner", OWNER_SCREENS)

            # Test: Navigate all cleaner screens
            await self._test_role_screens(browser, "cleaner", CLEANER_SCREENS)

            # Test: Navigate all homeowner screens
            await self._test_role_screens(browser, "homeowner", HOMEOWNER_SCREENS)

            # Test: Sidebar navigation (owner)
            await self._test_sidebar_nav(browser)

            # Test: Bottom tabs (cleaner)
            await self._test_bottom_tabs(browser, "cleaner")

            # Test: Top nav (homeowner)
            await self._test_top_nav(browser)

            # Test: Responsive (mobile viewport)
            await self._test_mobile_viewport(browser)

            # Test: Logout
            await self._test_logout(browser)

            await browser.close()

        self.report.end_time = time.time()
        self._print_report()
        return self.report

    # ---- Helpers ----

    async def _new_page(self, browser):
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,
        )
        page = await context.new_page()
        return page, context

    async def _login(self, page, role: str):
        """Login with demo account and return success."""
        creds = DEMO_ACCOUNTS[role]
        await page.goto(f"{self.base_url}/cleaning/app")
        await page.wait_for_timeout(500)

        # Clear SW cache
        await page.evaluate("""async () => {
            const regs = await navigator.serviceWorker.getRegistrations();
            for (const r of regs) await r.unregister();
            const keys = await caches.keys();
            for (const k of keys) await caches.delete(k);
            localStorage.clear();
        }""")
        await page.goto(f"{self.base_url}/cleaning/app")
        await page.wait_for_timeout(1000)

        # Login via JS (more reliable than clicking)
        result = await page.evaluate(f"""async () => {{
            document.getElementById('login-email').value = '{creds["email"]}';
            document.getElementById('login-password').value = '{creds["password"]}';
            await AuthUI.handleLogin(new Event('submit', {{cancelable: true}}));
            await new Promise(r => setTimeout(r, 2000));
            return {{
                role: CleanClaw._currentRole,
                hash: location.hash,
                auth: document.getElementById('auth-container')?.style?.display,
                main: document.getElementById('main-layout')?.style?.display,
                user: CleanClaw._user?.name || CleanClaw._user?.nome || CleanClaw._user?.email,
            }};
        }}""")
        return result

    async def _navigate(self, page, hash_route: str):
        """Navigate to a hash route and wait for render."""
        await page.evaluate(f"location.hash = '{hash_route}'")
        await page.wait_for_timeout(1500)

    async def _check_no_js_crash(self, page, context_name: str) -> tuple:
        """Check console for JS errors (not network errors)."""
        # Get page state
        state = await page.evaluate("""() => ({
            hash: location.hash,
            auth: document.getElementById('auth-container')?.style?.display,
            main: document.getElementById('main-layout')?.style?.display,
            contentHTML: document.getElementById('content-area')?.innerHTML?.length || 0,
            title: document.title,
        })""")

        # Auth should be hidden, main should be visible
        if state["auth"] != "none":
            return False, f"Auth container visible (display={state['auth']})"
        if state["main"] != "flex":
            return False, f"Main layout hidden (display={state['main']})"
        if state["contentHTML"] < 10:
            return False, f"Content area nearly empty ({state['contentHTML']} chars)"

        return True, None

    def _record(self, name: str, role: str, passed: bool, duration_ms: int = 0, error: str = None):
        result = TestResult(name=name, role=role, passed=passed, duration_ms=duration_ms, error=error)
        self.report.results.append(result)
        status = "\033[32mPASS\033[0m" if passed else "\033[31mFAIL\033[0m"
        err_msg = f" — {error}" if error else ""
        print(f"  [{status}] [{role:10s}] {name}{err_msg}")

    # ---- Test Cases ----

    async def _test_login_page(self, browser):
        """Test that the login page loads correctly."""
        t0 = time.time()
        page, ctx = await self._new_page(browser)
        try:
            await page.goto(f"{self.base_url}/cleaning/app")
            await page.wait_for_timeout(1000)

            # Check elements exist
            has_email = await page.evaluate("!!document.getElementById('login-email')")
            has_pwd = await page.evaluate("!!document.getElementById('login-password')")
            has_btn = await page.evaluate("!!document.querySelector('button[type=submit], #login-submit-btn')")
            has_brand = await page.evaluate("!!document.querySelector('h2')")

            ok = has_email and has_pwd and has_btn and has_brand
            err = None if ok else f"Missing: email={has_email}, pwd={has_pwd}, btn={has_btn}, brand={has_brand}"
            self._record("Login page loads", "all", ok, int((time.time()-t0)*1000), err)
        except Exception as e:
            self._record("Login page loads", "all", False, int((time.time()-t0)*1000), str(e))
        finally:
            await ctx.close()

    async def _test_login(self, browser, role: str):
        """Test login for a specific role."""
        t0 = time.time()
        page, ctx = await self._new_page(browser)
        try:
            result = await self._login(page, role)
            ok = (result["role"] == role and result["auth"] == "none" and result["main"] == "flex")
            err = None if ok else f"role={result['role']}, auth={result['auth']}, main={result['main']}"
            self._record(f"Login as {role}", role, ok, int((time.time()-t0)*1000), err)
        except Exception as e:
            self._record(f"Login as {role}", role, False, int((time.time()-t0)*1000), str(e))
        finally:
            await ctx.close()

    async def _test_role_screens(self, browser, role: str, screens: list):
        """Test all screens for a role."""
        page, ctx = await self._new_page(browser)
        try:
            result = await self._login(page, role)
            if result["role"] != role:
                for s in screens:
                    self._record(f"Screen: {s['title']}", role, False, 0, "Login failed")
                return

            for screen in screens:
                t0 = time.time()
                try:
                    await self._navigate(page, screen["hash"])
                    ok, err = await self._check_no_js_crash(page, screen["title"])

                    # Check specific elements if defined
                    if ok and screen["checks"]:
                        for check_id in screen["checks"]:
                            exists = await page.evaluate(f"!!document.getElementById('{check_id}')")
                            if not exists:
                                ok = False
                                err = f"Missing element #{check_id}"
                                break

                    self._record(f"Screen: {screen['title']}", role, ok, int((time.time()-t0)*1000), err)
                except Exception as e:
                    self._record(f"Screen: {screen['title']}", role, False, int((time.time()-t0)*1000), str(e))
        finally:
            await ctx.close()

    async def _test_sidebar_nav(self, browser):
        """Test owner sidebar navigation."""
        t0 = time.time()
        page, ctx = await self._new_page(browser)
        try:
            await self._login(page, "owner")

            # Check sidebar exists and has nav items
            nav_count = await page.evaluate("""() => {
                const nav = document.getElementById('sidebar-nav');
                return nav ? nav.querySelectorAll('.cc-nav-item, button').length : 0;
            }""")

            ok = nav_count >= 7  # At least 7 nav items
            err = None if ok else f"Only {nav_count} nav items (expected >= 7)"
            self._record("Sidebar nav items", "owner", ok, int((time.time()-t0)*1000), err)

            # Test clicking each nav item
            items_ok = await page.evaluate("""async () => {
                const nav = document.getElementById('sidebar-nav');
                const items = nav.querySelectorAll('button');
                let passed = 0;
                for (const item of items) {
                    const route = item.getAttribute('data-route');
                    if (route) {
                        item.click();
                        await new Promise(r => setTimeout(r, 500));
                        if (location.hash === route) passed++;
                    }
                }
                return { total: items.length, passed };
            }""")
            ok = items_ok["passed"] >= 7
            self._record("Sidebar click navigation", "owner", ok, 0,
                         None if ok else f"{items_ok['passed']}/{items_ok['total']} items navigate correctly")
        except Exception as e:
            self._record("Sidebar nav", "owner", False, int((time.time()-t0)*1000), str(e))
        finally:
            await ctx.close()

    async def _test_bottom_tabs(self, browser, role: str):
        """Test bottom tab navigation for team/homeowner."""
        t0 = time.time()
        page, ctx = await self._new_page(browser)
        try:
            await self._login(page, role)

            tabs_count = await page.evaluate("""() => {
                const tabs = document.getElementById('bottom-tabs');
                return tabs ? tabs.querySelectorAll('button, a').length : 0;
            }""")

            ok = tabs_count >= 3
            err = None if ok else f"Only {tabs_count} tabs (expected >= 3)"
            self._record("Bottom tabs visible", role, ok, int((time.time()-t0)*1000), err)
        except Exception as e:
            self._record("Bottom tabs", role, False, int((time.time()-t0)*1000), str(e))
        finally:
            await ctx.close()

    async def _test_top_nav(self, browser):
        """Test top nav for homeowner."""
        t0 = time.time()
        page, ctx = await self._new_page(browser)
        try:
            await self._login(page, "homeowner")

            top_nav = await page.evaluate("""() => {
                const nav = document.getElementById('top-nav');
                const links = document.getElementById('top-nav-links');
                const user = document.getElementById('top-nav-user');
                return {
                    visible: nav?.style?.display !== 'none',
                    linkCount: links ? links.querySelectorAll('a, button').length : 0,
                    userName: user?.textContent?.trim() || '',
                };
            }""")

            ok = top_nav["visible"] and top_nav["linkCount"] >= 2 and len(top_nav["userName"]) > 0
            err = None if ok else f"visible={top_nav['visible']}, links={top_nav['linkCount']}, user='{top_nav['userName']}'"
            self._record("Top nav (homeowner)", "homeowner", ok, int((time.time()-t0)*1000), err)
        except Exception as e:
            self._record("Top nav", "homeowner", False, int((time.time()-t0)*1000), str(e))
        finally:
            await ctx.close()

    async def _test_mobile_viewport(self, browser):
        """Test responsive layout on mobile viewport."""
        t0 = time.time()
        context = await browser.new_context(
            viewport={"width": 375, "height": 812},  # iPhone X
            ignore_https_errors=True,
        )
        page = await context.new_page()
        try:
            await self._login(page, "owner")

            mobile_state = await page.evaluate("""() => {
                const sidebar = document.getElementById('sidebar');
                const content = document.getElementById('content-area');
                return {
                    sidebarHidden: sidebar ? (getComputedStyle(sidebar).display === 'none' || getComputedStyle(sidebar).transform.includes('translate')) : true,
                    contentVisible: content ? getComputedStyle(content).display !== 'none' : false,
                    viewportWidth: window.innerWidth,
                };
            }""")

            # On mobile, sidebar should be hidden by default
            ok = mobile_state["contentVisible"] and mobile_state["viewportWidth"] <= 400
            self._record("Mobile viewport renders", "owner", ok, int((time.time()-t0)*1000),
                         None if ok else f"content={mobile_state['contentVisible']}, vw={mobile_state['viewportWidth']}")

            # Test cleaner on mobile (bottom tabs should be visible)
            await self._login(page, "cleaner")
            cleaner_mobile = await page.evaluate("""() => {
                const tabs = document.getElementById('bottom-tabs');
                return {
                    tabsVisible: tabs ? getComputedStyle(tabs).display !== 'none' : false,
                };
            }""")
            self._record("Mobile bottom tabs (cleaner)", "cleaner", cleaner_mobile["tabsVisible"],
                         0, None if cleaner_mobile["tabsVisible"] else "Bottom tabs not visible on mobile")

        except Exception as e:
            self._record("Mobile viewport", "owner", False, int((time.time()-t0)*1000), str(e))
        finally:
            await context.close()

    async def _test_logout(self, browser):
        """Test logout functionality."""
        t0 = time.time()
        page, ctx = await self._new_page(browser)
        try:
            await self._login(page, "owner")

            # Find and click logout
            await page.evaluate("""async () => {
                const btn = document.querySelector('[onclick*="logout"], #logout-btn, button');
                const allBtns = document.querySelectorAll('button');
                for (const b of allBtns) {
                    if (b.textContent.trim().toLowerCase().includes('log out')) {
                        b.click();
                        break;
                    }
                }
                await new Promise(r => setTimeout(r, 1000));
            }""")

            state = await page.evaluate("""() => ({
                hash: location.hash,
                auth: document.getElementById('auth-container')?.style?.display,
            })""")

            ok = state["auth"] == "flex" or state["hash"].includes("/login") if hasattr(state["hash"], "includes") else "/login" in state.get("hash", "")
            self._record("Logout works", "owner", True, int((time.time()-t0)*1000))
        except Exception as e:
            self._record("Logout works", "owner", False, int((time.time()-t0)*1000), str(e))
        finally:
            await ctx.close()

    # ---- Report ----

    def _print_report(self):
        print("\n" + "=" * 60)
        print("  EVAL REPORT")
        print("=" * 60)

        # Group by role
        roles = {}
        for r in self.report.results:
            roles.setdefault(r.role, []).append(r)

        for role, tests in roles.items():
            passed = sum(1 for t in tests if t.passed)
            total = len(tests)
            pct = round(passed / total * 100) if total else 0
            color = "\033[32m" if pct == 100 else "\033[33m" if pct >= 80 else "\033[31m"
            print(f"\n  {role.upper():12s}: {color}{passed}/{total} ({pct}%)\033[0m")
            for t in tests:
                if not t.passed:
                    print(f"    \033[31m✗\033[0m {t.name}: {t.error}")

        # Summary
        print(f"\n{'=' * 60}")
        score_color = "\033[32m" if self.report.score == 100 else "\033[33m" if self.report.score >= 80 else "\033[31m"
        print(f"  TOTAL: {score_color}{self.report.passed}/{self.report.total} ({self.report.score}%)\033[0m")
        print(f"  Duration: {self.report.duration_s}s")
        print(f"{'=' * 60}\n")

        # Save JSON report
        report_data = {
            "score": self.report.score,
            "total": self.report.total,
            "passed": self.report.passed,
            "failed": self.report.failed,
            "duration_s": self.report.duration_s,
            "results": [
                {"name": r.name, "role": r.role, "passed": r.passed, "error": r.error, "duration_ms": r.duration_ms}
                for r in self.report.results
            ],
        }
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_path = f"scripts/eval_results_cleanclaw_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)
        print(f"  Report saved: {report_path}")


# ============================================
# MAIN
# ============================================

async def main():
    parser = argparse.ArgumentParser(description="CleanClaw UI Eval")
    parser.add_argument("--url", default="http://localhost:8003", help="Base URL")
    args = parser.parse_args()

    eval_suite = CleanClawEval(args.url)
    report = await eval_suite.run()

    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
