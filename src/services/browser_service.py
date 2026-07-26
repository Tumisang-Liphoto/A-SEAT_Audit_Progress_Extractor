import webbrowser

from src.services.aseat_url_service import ASeatUrlService


class BrowserService:
    """Open A-SEAT using the user's default browser."""

    @staticmethod
    def normalise_url(url: str) -> str:
        """Resolve the configured address to the A-SEAT login page."""

        if not url.strip():
            return ""

        return ASeatUrlService.resolve(url).login_url

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check whether the supplied address resolves successfully."""

        try:
            ASeatUrlService.resolve(url)
            return True
        except ValueError:
            return False

    def open_url(self, url: str) -> tuple[bool, str]:
        """Open the resolved A-SEAT login page."""

        try:
            resolved_url = ASeatUrlService.resolve(url).login_url
        except ValueError as error:
            return False, str(error)

        try:
            opened = webbrowser.open(
                resolved_url,
                new=2,
                autoraise=True,
            )

            if not opened:
                return False, "Windows could not open the default web browser."

            return True, resolved_url

        except webbrowser.Error as error:
            return False, f"Browser error: {error}"

        except OSError as error:
            return False, f"Windows could not open the browser: {error}"
