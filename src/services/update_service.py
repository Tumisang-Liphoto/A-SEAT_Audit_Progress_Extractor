import hashlib
import shutil
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests
from packaging.version import InvalidVersion, Version

from src.utils.app_paths import update_workspace
from src.utils.version import APP_VERSION


ProgressCallback = Callable[[int, str], None]


class UpdateService:
    """Checks, downloads and prepares GitHub application updates."""

    REPOSITORY_OWNER = "Tumisang-Liphoto"
    REPOSITORY_NAME = "A-SEAT_Audit_Progress_Extractor"

    LATEST_RELEASE_URL = (
        "https://api.github.com/repos/"
        f"{REPOSITORY_OWNER}/{REPOSITORY_NAME}/releases/latest"
    )

    DOWNLOAD_CHUNK_SIZE = 1024 * 1024

    def _request_headers(self) -> dict[str, str]:
        """Return standard headers for GitHub requests."""

        return {
            "Accept": "application/vnd.github+json",
            "User-Agent": (
                "A-SEAT-Audit-Progress-Extractor/"
                f"{APP_VERSION}"
            ),
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def check_for_update(
        self,
        timeout_seconds: int = 15,
    ) -> dict[str, Any]:
        """Return details about the latest published GitHub release."""

        try:
            response = requests.get(
                self.LATEST_RELEASE_URL,
                timeout=timeout_seconds,
                headers=self._request_headers(),
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
                "The latest GitHub release does not contain "
                "a version tag."
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

        release_assets: list[dict[str, Any]] = []

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
                    ).strip(),
                    "download_url": str(
                        asset.get(
                            "browser_download_url",
                            "",
                        )
                    ).strip(),
                    "size": int(
                        asset.get(
                            "size",
                            0,
                        )
                        or 0
                    ),
                    "content_type": str(
                        asset.get(
                            "content_type",
                            "",
                        )
                    ).strip(),
                    "digest": str(
                        asset.get(
                            "digest",
                            "",
                        )
                    ).strip(),
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

    def prepare_update(
        self,
        release_information: dict[str, Any],
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        """Download, verify and safely extract an update package."""

        latest_version = str(
            release_information.get(
                "latest_version",
                "",
            )
        ).strip()

        if not latest_version:
            raise RuntimeError(
                "The update version could not be determined."
            )

        assets = release_information.get(
            "assets",
            [],
        )

        if not isinstance(
            assets,
            list,
        ):
            raise RuntimeError(
                "The release assets are not valid."
            )

        zip_asset = self._find_zip_asset(
            assets=assets,
            latest_version=latest_version,
        )

        checksum_asset = self._find_checksum_asset(
            assets=assets,
            zip_name=str(
                zip_asset["name"]
            ),
        )

        workspace = update_workspace()
        download_folder = workspace / "downloads"
        extraction_folder = workspace / "extracted"

        self.cleanup_workspace()

        download_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        extraction_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        zip_path = (
            download_folder
            / str(zip_asset["name"])
        )

        checksum_path = (
            download_folder
            / str(checksum_asset["name"])
        )

        try:
            self._report_progress(
                progress_callback,
                5,
                "Preparing update download",
            )

            self._download_file(
                url=str(
                    zip_asset["download_url"]
                ),
                destination=zip_path,
                start_percentage=10,
                end_percentage=65,
                progress_callback=progress_callback,
            )

            self._report_progress(
                progress_callback,
                68,
                "Downloading checksum",
            )

            self._download_file(
                url=str(
                    checksum_asset["download_url"]
                ),
                destination=checksum_path,
                start_percentage=68,
                end_percentage=73,
                progress_callback=progress_callback,
            )

            self._report_progress(
                progress_callback,
                75,
                "Verifying downloaded update",
            )

            expected_hash = self._read_checksum(
                checksum_path=checksum_path,
                expected_filename=zip_path.name,
            )

            actual_hash = self._calculate_sha256(
                zip_path
            )

            if actual_hash.lower() != expected_hash.lower():
                raise RuntimeError(
                    "The downloaded update failed its security "
                    "verification. The file will not be installed."
                )

            self._report_progress(
                progress_callback,
                82,
                "Extracting update package",
            )

            self._safe_extract_zip(
                zip_path=zip_path,
                destination=extraction_folder,
            )

            payload_folder = self._find_payload_folder(
                extraction_folder
            )

            executable_path = (
                payload_folder
                / "A-SEAT Audit Progress Extractor.exe"
            )

            internal_folder = (
                payload_folder
                / "_internal"
            )

            if not executable_path.is_file():
                raise RuntimeError(
                    "The update package does not contain the "
                    "application executable."
                )

            if not internal_folder.is_dir():
                raise RuntimeError(
                    "The update package does not contain the "
                    "required _internal folder."
                )

            self._report_progress(
                progress_callback,
                100,
                "Update downloaded and verified",
            )

            return {
                "latest_version": latest_version,
                "workspace": str(
                    workspace
                ),
                "zip_path": str(
                    zip_path
                ),
                "checksum_path": str(
                    checksum_path
                ),
                "extraction_folder": str(
                    extraction_folder
                ),
                "payload_folder": str(
                    payload_folder
                ),
                "executable_path": str(
                    executable_path
                ),
            }

        except Exception:
            self.cleanup_workspace()
            raise

    def cleanup_workspace(self) -> None:
        """Delete downloaded and extracted temporary update files."""

        workspace = update_workspace()

        if not workspace.exists():
            return

        try:
            shutil.rmtree(
                workspace
            )

        except OSError as error:
            raise RuntimeError(
                "The old temporary update files could not be removed."
            ) from error

    @staticmethod
    def _find_zip_asset(
        assets: list[dict[str, Any]],
        latest_version: str,
    ) -> dict[str, Any]:
        """Find the application ZIP for the specified release."""

        preferred_names = {
            (
                "A-SEAT_Audit_Progress_Extractor_"
                f"{latest_version}.zip"
            ).lower(),
            (
                "A-SEAT-Audit-Progress-Extractor-"
                f"{latest_version}.zip"
            ).lower(),
        }

        zip_assets = [
            asset
            for asset in assets
            if str(
                asset.get(
                    "name",
                    "",
                )
            ).lower().endswith(".zip")
        ]

        for asset in zip_assets:
            asset_name = str(
                asset.get(
                    "name",
                    "",
                )
            ).lower()

            if asset_name in preferred_names:
                UpdateService._validate_asset(
                    asset,
                    "application ZIP",
                )
                return asset

        if len(zip_assets) == 1:
            UpdateService._validate_asset(
                zip_assets[0],
                "application ZIP",
            )
            return zip_assets[0]

        raise RuntimeError(
            "The GitHub release does not contain a clearly "
            "identified application ZIP package."
        )

    @staticmethod
    def _find_checksum_asset(
        assets: list[dict[str, Any]],
        zip_name: str,
    ) -> dict[str, Any]:
        """Find the SHA-256 checksum file for the ZIP."""

        preferred_names = {
            f"{zip_name}.sha256".lower(),
            f"{zip_name}.sha256.txt".lower(),
            "sha256sums.txt",
            "checksums.txt",
        }

        checksum_assets = [
            asset
            for asset in assets
            if str(
                asset.get(
                    "name",
                    "",
                )
            ).lower() in preferred_names
        ]

        if not checksum_assets:
            raise RuntimeError(
                "The GitHub release does not contain a SHA-256 "
                "checksum file for the update package."
            )

        checksum_asset = checksum_assets[0]

        UpdateService._validate_asset(
            checksum_asset,
            "checksum file",
        )

        return checksum_asset

    @staticmethod
    def _validate_asset(
        asset: dict[str, Any],
        description: str,
    ) -> None:
        """Validate required release-asset information."""

        asset_name = str(
            asset.get(
                "name",
                "",
            )
        ).strip()

        download_url = str(
            asset.get(
                "download_url",
                "",
            )
        ).strip()

        if not asset_name or not download_url:
            raise RuntimeError(
                f"The release {description} is missing "
                "required information."
            )

    def _download_file(
        self,
        url: str,
        destination: Path,
        start_percentage: int,
        end_percentage: int,
        progress_callback: ProgressCallback | None,
        timeout_seconds: int = 60,
    ) -> None:
        """Download a release asset while reporting progress."""

        try:
            with requests.get(
                url,
                stream=True,
                timeout=timeout_seconds,
                headers=self._request_headers(),
            ) as response:
                if response.status_code >= 400:
                    raise RuntimeError(
                        "GitHub returned "
                        f"HTTP {response.status_code} while "
                        "downloading the update."
                    )

                total_size = int(
                    response.headers.get(
                        "Content-Length",
                        0,
                    )
                    or 0
                )

                downloaded_size = 0

                with destination.open(
                    "wb"
                ) as file:
                    for chunk in response.iter_content(
                        chunk_size=self.DOWNLOAD_CHUNK_SIZE
                    ):
                        if not chunk:
                            continue

                        file.write(
                            chunk
                        )

                        downloaded_size += len(
                            chunk
                        )

                        if total_size > 0:
                            portion = (
                                downloaded_size
                                / total_size
                            )

                            percentage = int(
                                start_percentage
                                + (
                                    end_percentage
                                    - start_percentage
                                )
                                * portion
                            )

                            percentage = min(
                                percentage,
                                end_percentage,
                            )

                            self._report_progress(
                                progress_callback,
                                percentage,
                                (
                                    f"Downloading {destination.name}"
                                ),
                            )

        except requests.exceptions.Timeout as error:
            raise RuntimeError(
                "The update download timed out."
            ) from error

        except requests.exceptions.ConnectionError as error:
            raise RuntimeError(
                "The update download failed because GitHub "
                "could not be reached."
            ) from error

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"The update download failed: {error}"
            ) from error

        except OSError as error:
            raise RuntimeError(
                "The update file could not be saved to disk."
            ) from error

        if not destination.is_file():
            raise RuntimeError(
                "The update download did not create a file."
            )

        if destination.stat().st_size == 0:
            raise RuntimeError(
                "The downloaded update file is empty."
            )

    @staticmethod
    def _read_checksum(
        checksum_path: Path,
        expected_filename: str,
    ) -> str:
        """Read a SHA-256 value from the downloaded checksum file."""

        try:
            lines = checksum_path.read_text(
                encoding="utf-8",
            ).splitlines()

        except OSError as error:
            raise RuntimeError(
                "The checksum file could not be read."
            ) from error

        for line in lines:
            cleaned_line = line.strip()

            if not cleaned_line:
                continue

            parts = cleaned_line.replace(
                "*",
                " ",
            ).split()

            if not parts:
                continue

            possible_hash = parts[0].strip()

            if (
                len(possible_hash) == 64
                and all(
                    character in "0123456789abcdefABCDEF"
                    for character in possible_hash
                )
            ):
                if len(parts) == 1:
                    return possible_hash

                listed_filename = parts[-1].strip()

                if (
                    listed_filename.lower()
                    == expected_filename.lower()
                ):
                    return possible_hash

        raise RuntimeError(
            "The checksum file does not contain a valid "
            "SHA-256 value for the update package."
        )

    @staticmethod
    def _calculate_sha256(
        file_path: Path,
    ) -> str:
        """Calculate the SHA-256 digest of a file."""

        digest = hashlib.sha256()

        try:
            with file_path.open(
                "rb"
            ) as file:
                while True:
                    block = file.read(
                        1024 * 1024
                    )

                    if not block:
                        break

                    digest.update(
                        block
                    )

        except OSError as error:
            raise RuntimeError(
                "The downloaded update could not be verified."
            ) from error

        return digest.hexdigest()

    @staticmethod
    def _safe_extract_zip(
        zip_path: Path,
        destination: Path,
    ) -> None:
        """Extract a ZIP while preventing path traversal."""

        destination_root = destination.resolve()

        try:
            with zipfile.ZipFile(
                zip_path,
                "r",
            ) as archive:
                for member in archive.infolist():
                    member_path = (
                        destination
                        / member.filename
                    ).resolve()

                    try:
                        member_path.relative_to(
                            destination_root
                        )

                    except ValueError as error:
                        raise RuntimeError(
                            "The update archive contains an unsafe path."
                        ) from error

                archive.extractall(
                    destination
                )

        except zipfile.BadZipFile as error:
            raise RuntimeError(
                "The downloaded update package is not a valid ZIP file."
            ) from error

        except OSError as error:
            raise RuntimeError(
                "The update package could not be extracted."
            ) from error

    @staticmethod
    def _find_payload_folder(
        extraction_folder: Path,
    ) -> Path:
        """Locate the folder containing the packaged application."""

        direct_executable = (
            extraction_folder
            / "A-SEAT Audit Progress Extractor.exe"
        )

        if direct_executable.is_file():
            return extraction_folder

        candidate_folders = [
            item
            for item in extraction_folder.iterdir()
            if item.is_dir()
        ]

        for candidate in candidate_folders:
            executable = (
                candidate
                / "A-SEAT Audit Progress Extractor.exe"
            )

            if executable.is_file():
                return candidate

        raise RuntimeError(
            "The extracted update package does not contain "
            "the expected application folder."
        )

    @staticmethod
    def _report_progress(
        callback: ProgressCallback | None,
        percentage: int,
        message: str,
    ) -> None:
        """Report progress when a callback was supplied."""

        if callback is not None:
            callback(
                percentage,
                message,
            )