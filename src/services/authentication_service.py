from __future__ import annotations

import time
from typing import Any

from playwright.sync_api import sync_playwright

from src.services.aseat_url_service import ASeatUrlService


class AuthenticationService:
    """Validate A-SEAT credentials without extracting audit data."""

    USERNAME_SELECTOR = (
        "#user_login, input[name='user'], "
        "input[name='user_login']"
    )

    PASSWORD_SELECTOR = (
        "#user_pass, input[name='pwd'], "
        "input[name='user_pass'], input[type='password']"
    )

    SUBMIT_SELECTOR = (
        "#submit, form#loginform input[type='submit'], "
        "input[type='submit'][value='Login'], "
        "button[type='submit']"
    )

    @classmethod
    def authenticate(
        cls,
        *,
        configured_url: str,
        username: str,
        password: str,
        show_browser: bool = False,
    ) -> dict[str, Any]:
        """Open A-SEAT and confirm that the supplied credentials work."""

        clean_username = username.strip()

        if not clean_username:
            raise ValueError("A username is required.")

        if not password:
            raise ValueError("A password is required.")

        resolved = ASeatUrlService.resolve(
            configured_url
        )

        started_at = time.perf_counter()

        with sync_playwright() as playwright:
            browser = None

            try:
                browser = playwright.chromium.launch(
                    channel="msedge",
                    headless=not show_browser,
                )

                page = browser.new_page(
                    viewport={
                        "width": 1400,
                        "height": 900,
                    }
                )

                page.goto(
                    resolved.login_url,
                    wait_until="domcontentloaded",
                    timeout=60_000,
                )

                if page.locator(
                    "#logout_btn"
                ).count() == 0:
                    page.locator(
                        cls.USERNAME_SELECTOR
                    ).first.wait_for(
                        state="visible",
                        timeout=30_000,
                    )

                    page.locator(
                        cls.PASSWORD_SELECTOR
                    ).first.wait_for(
                        state="visible",
                        timeout=30_000,
                    )

                    page.locator(
                        cls.USERNAME_SELECTOR
                    ).first.fill(
                        clean_username
                    )

                    page.locator(
                        cls.PASSWORD_SELECTOR
                    ).first.fill(
                        password
                    )

                    submit_button = page.locator(
                        cls.SUBMIT_SELECTOR
                    ).first

                    if submit_button.count() == 0:
                        raise RuntimeError(
                            "The A-SEAT login button could not be detected."
                        )

                    submit_button.click()

                    try:
                        page.wait_for_load_state(
                            "domcontentloaded",
                            timeout=60_000,
                        )
                    except Exception:
                        pass

                    page.wait_for_timeout(
                        1_000
                    )

                login_form_visible = (
                    page.locator(
                        cls.USERNAME_SELECTOR
                    ).count() > 0
                    and page.locator(
                        cls.PASSWORD_SELECTOR
                    ).count() > 0
                )

                if login_form_visible:
                    login_error = ""

                    if page.locator(
                        "#login_status"
                    ).count() > 0:
                        login_error = (
                            page.locator(
                                "#login_status"
                            )
                            .inner_text()
                            .strip()
                        )

                    if login_error:
                        raise RuntimeError(
                            f"A-SEAT login failed: {login_error}"
                        )

                    raise RuntimeError(
                        "A-SEAT login was not successful. "
                        "Check the username and password."
                    )

                dashboard_detected = (
                    page.locator(
                        "#logout_btn"
                    ).count() > 0
                    or "/system/" in page.url.lower()
                )

                if not dashboard_detected:
                    raise RuntimeError(
                        "The credentials were submitted, but an "
                        "authenticated A-SEAT page was not confirmed."
                    )

                return {
                    "success": True,
                    "username": clean_username,
                    "final_url": page.url,
                    "resolved_login_url": (
                        resolved.login_url
                    ),
                    "resolved_dashboard_url": (
                        resolved.dashboard_url
                    ),
                    "response_time": (
                        time.perf_counter()
                        - started_at
                    ),
                    "message": (
                        "A-SEAT authentication was successful."
                    ),
                }

            finally:
                password = ""

                if browser is not None:
                    try:
                        browser.close()
                    except Exception:
                        pass
