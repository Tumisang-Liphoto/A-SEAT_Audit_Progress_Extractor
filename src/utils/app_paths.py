import sys
from pathlib import Path


def application_folder() -> Path:
    """Return the folder containing the packaged app or project."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]


def config_folder() -> Path:
    """Return the persistent configuration folder."""

    return application_folder() / "config"


def update_workspace() -> Path:
    """Return the temporary update workspace."""

    local_app_data = Path.home() / "AppData" / "Local"

    return (
        local_app_data
        / "A-SEAT Audit Progress Extractor"
        / "updates"
    )