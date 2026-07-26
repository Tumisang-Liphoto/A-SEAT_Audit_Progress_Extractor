import time
from typing import Any

import requests

from src.services.aseat_url_service import ASeatUrlService


class ConnectionService:
    """Test whether the configured A-SEAT system is reachable."""

    @classmethod
    def build_test_url(cls, configured_url: str) -> str:
        """Build the resolved A-SEAT login-page URL."""

        return ASeatUrlService.resolve(configured_url).login_url

    @staticmethod
    def _detect_login_page(
        html: str,
        system_name: str,
    ) -> tuple[bool, str]:
        """Confirm that the returned page contains an A-SEAT login form."""

        normalised_html = html.lower()

        username_markers = (
            'id="user_login"',
            "id='user_login'",
            'name="user"',
            "name='user'",
            'name="user_login"',
            "name='user_login'",
        )

        password_markers = (
            'id="user_pass"',
            "id='user_pass'",
            'name="pwd"',
            "name='pwd'",
            'name="user_pass"',
            "name='user_pass'",
        )

        submit_markers = (
            'id="submit"',
            "id='submit'",
            'id="loginform"',
            "id='loginform'",
            'value="login"',
            "value='login'",
        )

        has_username = any(
            marker in normalised_html
            for marker in username_markers
        )

        has_password = any(
            marker in normalised_html
            for marker in password_markers
        )

        has_submit = any(
            marker in normalised_html
            for marker in submit_markers
        )

        if has_username and has_password and has_submit:
            return True, f"{system_name} login page detected."

        if has_username and has_password:
            return True, f"{system_name} login fields detected."

        if has_username or has_password or has_submit:
            return (
                False,
                (
                    "The server responded and part of the login form "
                    "was detected, but the complete "
                    f"{system_name} login page was not confirmed."
                ),
            )

        system_name_marker = system_name.lower().strip()

        generic_system_markers = (
            "a-seat",
            "aseat",
            "/system/",
            "business_audit",
            "project_list.php",
            "user_login",
            "user_pass",
        )

        system_recognised = (
            bool(system_name_marker)
            and system_name_marker in normalised_html
        )

        generic_system_recognised = any(
            marker in normalised_html
            for marker in generic_system_markers
        )

        if system_recognised or generic_system_recognised:
            return (
                False,
                (
                    f"The {system_name} server appears reachable, "
                    "but the login page was not detected."
                ),
            )

        return (
            False,
            (
                "The server responded, but the returned page was not "
                f"recognised as the {system_name} login page."
            ),
        )

    def test_connection(
        self,
        configured_url: str,
        system_name: str = "A-SEAT",
        timeout_seconds: int = 15,
    ) -> dict[str, Any]:
        """Test whether the configured system login page is reachable."""

        display_name = system_name.strip() or "A-SEAT"

        resolved = ASeatUrlService.resolve(
            configured_url
        )

        test_url = resolved.login_url

        started_at = time.perf_counter()

        try:
            response = requests.get(
                test_url,
                timeout=timeout_seconds,
                allow_redirects=True,
                verify=True,
                headers={
                    "User-Agent": (
                        "A-SEAT-Audit-Progress-Extractor/0.1"
                    ),
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,*/*;q=0.8"
                    ),
                },
            )

        except requests.exceptions.SSLError as error:
            raise RuntimeError(
                (
                    f"The {display_name} server was reached, "
                    "but its SSL certificate could not be verified."
                )
            ) from error

        except requests.exceptions.ConnectTimeout as error:
            raise RuntimeError(
                (
                    "The connection attempt timed out before the "
                    f"{display_name} server could be reached."
                )
            ) from error

        except requests.exceptions.ReadTimeout as error:
            raise RuntimeError(
                (
                    f"The {display_name} server was reached, but it "
                    "did not respond within the allowed time."
                )
            ) from error

        except requests.exceptions.ConnectionError as error:
            raise RuntimeError(
                (
                    f"The {display_name} server could not be reached. "
                    "Check the URL, network connection and VPN access."
                )
            ) from error

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"The connection test failed: {error}"
            ) from error

        elapsed_seconds = (
            time.perf_counter()
            - started_at
        )

        if response.status_code >= 500:
            raise RuntimeError(
                (
                    f"The {display_name} server returned an internal "
                    f"server error: HTTP {response.status_code}."
                )
            )

        if response.status_code >= 400:
            raise RuntimeError(
                (
                    f"The {display_name} server returned "
                    f"HTTP {response.status_code}."
                )
            )

        login_detected, message = (
            self._detect_login_page(
                response.text,
                display_name,
            )
        )

        return {
            "success": login_detected,
            "status_code": response.status_code,
            "requested_url": test_url,
            "final_url": response.url,
            "resolved_login_url": resolved.login_url,
            "resolved_dashboard_url": resolved.dashboard_url,
            "response_time": elapsed_seconds,
            "message": message,
        }