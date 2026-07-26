import sys
from pathlib import Path

from PySide6.QtGui import QImageReader

from src.utils.app_paths import application_folder, config_folder


class BrandingService:
    """Manage the default and custom organisation logos."""

    DEFAULT_LOGO_FILENAME = "afroasi_e_logo.png"
    CUSTOM_LOGO_FILENAME = "custom_logo.png"

    SUPPORTED_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".ico",
    }

    def __init__(self) -> None:
        self.branding_folder = (
            config_folder()
            / "branding"
        )

        self.custom_logo_path = (
            self.branding_folder
            / self.CUSTOM_LOGO_FILENAME
        )

    def get_default_logo_path(self) -> Path:
        """Locate the packaged AFROSAI-E logo."""

        candidates = self._default_logo_candidates()

        for candidate in candidates:
            if candidate.is_file():
                return candidate

        raise FileNotFoundError(
            "The built-in AFROSAI-E logo could not be found."
        )

    def get_active_logo_path(
        self,
        use_custom_logo: bool,
    ) -> Path:
        """Return the active organisation logo path."""

        if (
            use_custom_logo
            and self.custom_logo_path.is_file()
        ):
            return self.custom_logo_path

        return self.get_default_logo_path()

    def has_custom_logo(self) -> bool:
        """Return whether a custom organisation logo exists."""

        return self.custom_logo_path.is_file()

    def install_custom_logo(
        self,
        source_path: str,
    ) -> Path:
        """
        Validate and copy an uploaded image into application storage.

        The image is normalised to PNG so the rest of the application
        always works with one predictable format.
        """

        source = Path(
            source_path
        ).expanduser()

        if not source.is_file():
            raise FileNotFoundError(
                "The selected logo file could not be found."
            )

        if (
            source.suffix.lower()
            not in self.SUPPORTED_EXTENSIONS
        ):
            raise ValueError(
                "Select a PNG, JPG, JPEG or ICO image."
            )

        reader = QImageReader(
            str(source)
        )
        reader.setAutoTransform(
            True
        )

        if not reader.canRead():
            raise ValueError(
                "The selected file is not a readable image."
            )

        image = reader.read()

        if image.isNull():
            raise ValueError(
                "The selected logo could not be loaded."
            )

        if (
            image.width() < 64
            or image.height() < 64
        ):
            raise ValueError(
                "The logo must be at least 64 by 64 pixels."
            )

        self.branding_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = (
            self.branding_folder
            / "custom_logo.tmp.png"
        )

        if not image.save(
            str(temporary_path),
            "PNG",
        ):
            raise RuntimeError(
                "The selected logo could not be saved."
            )

        temporary_path.replace(
            self.custom_logo_path
        )

        return self.custom_logo_path

    def restore_default_logo(self) -> None:
        """Remove the custom logo and restore the default logo."""

        if not self.custom_logo_path.exists():
            self._remove_empty_branding_folder()
            return

        try:
            self.custom_logo_path.unlink()
        except OSError as error:
            raise RuntimeError(
                "The custom logo could not be removed."
            ) from error

        self._remove_empty_branding_folder()

    def remove_custom_branding(self) -> None:
        """Remove custom branding during an application reset."""

        self.restore_default_logo()

    def _default_logo_candidates(
        self,
    ) -> list[Path]:
        """Build possible development and packaged asset locations."""

        relative_asset = (
            Path("assets")
            / "images"
            / self.DEFAULT_LOGO_FILENAME
        )

        candidates: list[Path] = []

        runtime_bundle = getattr(
            sys,
            "_MEIPASS",
            "",
        )

        if runtime_bundle:
            candidates.append(
                Path(runtime_bundle)
                / relative_asset
            )

        app_folder = application_folder()

        candidates.extend(
            [
                app_folder
                / relative_asset,
                app_folder
                / "_internal"
                / relative_asset,
                (
                    Path(__file__)
                    .resolve()
                    .parents[2]
                    / relative_asset
                ),
            ]
        )

        unique_candidates: list[Path] = []

        for candidate in candidates:
            if candidate not in unique_candidates:
                unique_candidates.append(
                    candidate
                )

        return unique_candidates

    def _remove_empty_branding_folder(self) -> None:
        """Remove the branding folder only when it is empty."""

        try:
            if (
                self.branding_folder.is_dir()
                and not any(
                    self.branding_folder.iterdir()
                )
            ):
                self.branding_folder.rmdir()

        except OSError:
            pass