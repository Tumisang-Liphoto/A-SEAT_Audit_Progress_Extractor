import webbrowser
from urllib.parse import urlparse


class BrowserService:
    """Opens web addresses using the user's default browser."""

    @staticmethod
    def normalise_url(url: str) -> str:
        """Add HTTPS when the user enters an address without a scheme."""

        cleaned_url = url.strip()

        if not cleaned_url:
            return ""

        parsed_url = urlparse(cleaned_url)

        if not parsed_url.scheme:
            cleaned_url = f"https://{cleaned_url}"

        return cleaned_url

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check whether the supplied address is a usable HTTP or HTTPS URL."""

        if not url:
            return False

        parsed_url = urlparse(url)

        return (
            parsed_url.scheme in {"http", "https"}
            and bool(parsed_url.netloc)
        )

    def open_url(self, url: str) -> tuple[bool, str]:
        """Open a URL in the default browser."""

        normalised_url = self.normalise_url(url)

        if not self.is_valid_url(normalised_url):
            return False, "The configured A-SEAT address is not valid."

        try:
            opened = webbrowser.open(
                normalised_url,
                new=2,
                autoraise=True,
            )

            if not opened:
                return (
                    False,
                    "Windows could not open the default web browser.",
                )

            return True, normalised_url

        except webbrowser.Error as error:
            return False, f"Browser error: {error}"

        except OSError as error:
            return False, f"Windows could not open the browser: {error}"