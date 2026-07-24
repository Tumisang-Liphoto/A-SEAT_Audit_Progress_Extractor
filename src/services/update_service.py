from typing import Any

import requests
from packaging.version import InvalidVersion, Version

from src.utils.version import APP_VERSION


class UpdateService:
    """Checks GitHub Releases for a newer application version."""

    REPOSITORY_OWNER = "Tumisang-Liphoto"
    REPOSITORY_NAME = "A-SEAT_Audit_Progress_Extractor"

    LATEST_RELEASE_URL = (
        "https://api.github.com/repos/"
        f"{REPOSITORY_OWNER}/{REPOSITORY_NAME}/releases/latest"
    )

    def check_for_update(
        self,
        timeout_seconds: int = 15,
    ) -> dict[str, Any]:
        """Return details about the latest published GitHub release."""

        try:
            response = requests.get(
                self.LATEST_RELEASE_URL,
                timeout=timeout_seconds,
                headers={
                    "Accept": (
                        "application/vnd.github+json"
                    ),
                    "User-Agent": (
                        "A-SEAT-Audit-Progress-Extractor/"
                        f"{APP_VERSION}"
                    ),
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

        except requests.exceptions.ConnectTimeout as error:
            raise RuntimeError(
                "The update check timed out before GitHub "
                "could be reached."
            ) from error

        except requests.exceptions.ReadTimeout as error:
            raise RuntimeError(
                "GitHub was reached, but it did not respond "
                "within the allowed time."
            ) from error

        except requests.exceptions.ConnectionError as error:
            raise RuntimeError(
                "GitHub could not be reached. Check your internet "
                "connection and try again."
            ) from error

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"The update check failed: {error}"
            ) from error

        if response.status_code == 404:
            raise RuntimeError(
                "No published GitHub release could be found."
            )

        if response.status_code >= 400:
            raise RuntimeError(
                "GitHub returned "
                f"HTTP {response.status_code} during the update check."
            )

        try:
            release_data = response.json()
        except ValueError as error:
            raise RuntimeError(
                "GitHub returned an invalid update response."
            ) from error

        tag_name = str(
            release_data.get(
                "tag_name",
                "",
            )
        ).strip()

        if not tag_name:
            raise RuntimeError(
                "The latest GitHub release does not contain a version tag."
            )

        latest_version_text = tag_name.lstrip(
            "vV"
        )

        try:
            current_version = Version(
                APP_VERSION
            )

            latest_version = Version(
                latest_version_text
            )

        except InvalidVersion as error:
            raise RuntimeError(
                "The application or GitHub release version "
                "is not in a valid format."
            ) from error

        release_assets = []

        for asset in release_data.get(
            "assets",
            [],
        ):
            release_assets.append(
                {
                    "name": str(
                        asset.get(
                            "name",
                            "",
                        )
                    ),
                    "download_url": str(
                        asset.get(
                            "browser_download_url",
                            "",
                        )
                    ),
                    "size": int(
                        asset.get(
                            "size",
                            0,
                        )
                        or 0
                    ),
                }
            )

        return {
            "update_available": (
                latest_version > current_version
            ),
            "current_version": str(
                current_version
            ),
            "latest_version": str(
                latest_version
            ),
            "tag_name": tag_name,
            "release_name": str(
                release_data.get(
                    "name",
                    tag_name,
                )
            ),
            "release_notes": str(
                release_data.get(
                    "body",
                    "",
                )
            ),
            "release_url": str(
                release_data.get(
                    "html_url",
                    "",
                )
            ),
            "published_at": str(
                release_data.get(
                    "published_at",
                    "",
                )
            ),
            "assets": release_assets,
        }