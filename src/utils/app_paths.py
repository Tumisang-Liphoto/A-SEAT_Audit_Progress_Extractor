import os
import sys
from pathlib import Path


APP_DATA_FOLDER_NAME = "A-SEAT Utility"


def application_folder() -> Path:
    """Return the folder containing the packaged app or project."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]


def local_app_data_folder() -> Path:
    """Return the current user's LocalAppData folder."""

    configured_path = os.environ.get("LOCALAPPDATA", "").strip()

    if configured_path:
        return Path(configured_path)

    return Path.home() / "AppData" / "Local"


def user_data_folder() -> Path:
    """Return the root folder for writable application data."""

    return local_app_data_folder() / APP_DATA_FOLDER_NAME


def config_folder() -> Path:
    """Return the per-user configuration folder."""

    return user_data_folder() / "config"


def history_folder() -> Path:
    """Return the per-user extraction and activity history folder."""

    return user_data_folder() / "history"


def logs_folder() -> Path:
    """Return the per-user application log folder."""

    return user_data_folder() / "logs"


def cache_folder() -> Path:
    """Return the per-user cache folder."""

    return user_data_folder() / "cache"


def temp_folder() -> Path:
    """Return the per-user temporary workspace."""

    return user_data_folder() / "temp"


def update_workspace() -> Path:
    """Return the per-user update workspace."""

    return user_data_folder() / "updates"


def branding_folder() -> Path:
    """Return the per-user custom branding folder."""

    return user_data_folder() / "branding"


def legacy_config_folder() -> Path:
    """Return the configuration folder used by versions up to 0.1.7."""

    return application_folder() / "config"


def ensure_user_data_folders() -> None:
    """Create the standard per-user writable folders."""

    for folder in (
        config_folder(),
        history_folder(),
        logs_folder(),
        cache_folder(),
        temp_folder(),
        update_workspace(),
        branding_folder(),
    ):
        folder.mkdir(parents=True, exist_ok=True)
