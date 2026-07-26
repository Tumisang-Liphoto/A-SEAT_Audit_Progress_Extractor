from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class ResolvedASeatUrls:
    """Resolved URLs for one A-SEAT installation."""

    configured_url: str
    origin_url: str
    login_url: str
    dashboard_url: str
    audit_list_url: str


class ASeatUrlService:
    """Normalise local and hosted A-SEAT addresses consistently."""

    LOGIN_PATH = "/system/"
    DASHBOARD_PATH = "/system/dashboard/"
    AUDIT_LIST_PATH = "/system/business_audit/project_list.php"

    @staticmethod
    def _is_ip_address(hostname: str) -> bool:
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            return False

    @classmethod
    def _add_default_scheme(cls, value: str) -> str:
        """Use HTTP for bare IP addresses and HTTPS for public hostnames."""

        candidate = value.strip()

        if re.match(r"^[a-z][a-z0-9+.-]*://", candidate, re.IGNORECASE):
            return candidate

        host_candidate = candidate.split("/", 1)[0]
        host_candidate = host_candidate.split(":", 1)[0].strip("[]").lower()

        if (
            host_candidate == "localhost"
            or host_candidate.endswith(".local")
            or cls._is_ip_address(host_candidate)
        ):
            return f"http://{candidate}"

        return f"https://{candidate}"

    @classmethod
    def resolve(cls, configured_url: str) -> ResolvedASeatUrls:
        """Resolve a user-entered address into A-SEAT application URLs."""

        cleaned_url = configured_url.strip()

        if not cleaned_url:
            raise ValueError("The A-SEAT URL has not been configured.")

        candidate_url = cls._add_default_scheme(cleaned_url)
        parsed = urlsplit(candidate_url)

        if parsed.scheme.lower() not in {"http", "https"}:
            raise ValueError("The A-SEAT address must use HTTP or HTTPS.")

        if not parsed.hostname:
            raise ValueError("The configured A-SEAT address is not valid.")

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc

        origin_url = urlunsplit((scheme, netloc, "", "", ""))

        def build(path: str) -> str:
            return urlunsplit((scheme, netloc, path, "", ""))

        return ResolvedASeatUrls(
            configured_url=cleaned_url,
            origin_url=origin_url,
            login_url=build(cls.LOGIN_PATH),
            dashboard_url=build(cls.DASHBOARD_PATH),
            audit_list_url=build(cls.AUDIT_LIST_PATH),
        )

    @classmethod
    def normalise_configured_url(cls, configured_url: str) -> str:
        """Return the canonical A-SEAT login URL for saving or display."""

        return cls.resolve(configured_url).login_url