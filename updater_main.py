import argparse
import ctypes
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


APPLICATION_EXE_NAME = "A-SEAT Audit Progress Extractor.exe"
UPDATER_EXE_NAME = "A-SEAT Updater.exe"

WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
SYNCHRONIZE = 0x00100000


def configure_logging(workspace: Path) -> None:
    """Create an updater log in the temporary update workspace."""

    workspace.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = workspace / "updater.log"

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | %(message)s"
        ),
        handlers=[
            logging.FileHandler(
                log_file,
                encoding="utf-8",
            )
        ],
    )


def wait_for_process_to_exit(
    process_id: int,
    timeout_seconds: int = 90,
) -> None:
    """Wait for the main application process to close."""

    if process_id <= 0:
        return

    process_handle = ctypes.windll.kernel32.OpenProcess(
        SYNCHRONIZE,
        False,
        process_id,
    )

    if not process_handle:
        logging.info(
            "The main application process is already closed."
        )
        return

    try:
        timeout_milliseconds = (
            timeout_seconds * 1000
        )

        result = ctypes.windll.kernel32.WaitForSingleObject(
            process_handle,
            timeout_milliseconds,
        )

        if result == WAIT_OBJECT_0:
            logging.info(
                "The main application closed successfully."
            )
            return

        if result == WAIT_TIMEOUT:
            raise RuntimeError(
                "The main application did not close within "
                "the allowed time."
            )

        raise RuntimeError(
            "Windows returned an unexpected result while "
            "waiting for the application to close."
        )

    finally:
        ctypes.windll.kernel32.CloseHandle(
            process_handle
        )


def validate_paths(
    source_folder: Path,
    target_folder: Path,
    workspace: Path,
) -> None:
    """Validate the update source and installation locations."""

    source_folder = source_folder.resolve()
    target_folder = target_folder.resolve()
    workspace = workspace.resolve()

    if not source_folder.is_dir():
        raise RuntimeError(
            "The extracted update folder does not exist."
        )

    source_executable = (
        source_folder
        / APPLICATION_EXE_NAME
    )

    source_internal = (
        source_folder
        / "_internal"
    )

    if not source_executable.is_file():
        raise RuntimeError(
            "The update package does not contain the "
            "application executable."
        )

    if not source_internal.is_dir():
        raise RuntimeError(
            "The update package does not contain the "
            "required _internal folder."
        )

    if not target_folder.is_dir():
        raise RuntimeError(
            "The current application folder does not exist."
        )

    target_executable = (
        target_folder
        / APPLICATION_EXE_NAME
    )

    if not target_executable.is_file():
        raise RuntimeError(
            "The current application executable could not "
            "be found."
        )

    if source_folder == target_folder:
        raise RuntimeError(
            "The update source and application folders "
            "cannot be the same."
        )

    try:
        source_folder.relative_to(
            target_folder
        )
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "The extracted update package cannot be located "
            "inside the application folder."
        )

    try:
        workspace.relative_to(
            target_folder
        )
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "The update workspace cannot be located inside "
            "the application folder."
        )


def remove_path(path: Path) -> None:
    """Delete a file or directory when it exists."""

    if not path.exists():
        return

    if path.is_dir():
        shutil.rmtree(
            path
        )
    else:
        path.unlink()


def copy_item(
    source: Path,
    destination: Path,
) -> None:
    """Copy one file or directory."""

    if source.is_dir():
        shutil.copytree(
            source,
            destination,
        )
    else:
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            destination,
        )


def create_backup(
    target_folder: Path,
    backup_folder: Path,
) -> None:
    """Back up the current application while excluding config."""

    logging.info(
        "Creating application backup."
    )

    remove_path(
        backup_folder
    )

    backup_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    for item in target_folder.iterdir():
        if item.name.lower() == "config":
            continue

        destination = (
            backup_folder
            / item.name
        )

        copy_item(
            item,
            destination,
        )

    logging.info(
        "Application backup completed."
    )


def clear_application_files(
    target_folder: Path,
) -> None:
    """Delete old application files while preserving config."""

    logging.info(
        "Removing old application files."
    )

    for item in target_folder.iterdir():
        if item.name.lower() == "config":
            continue

        remove_path(
            item
        )


def install_update(
    source_folder: Path,
    target_folder: Path,
) -> None:
    """Copy the new application files into place."""

    logging.info(
        "Installing new application files."
    )

    clear_application_files(
        target_folder
    )

    for item in source_folder.iterdir():
        item_name = item.name.lower()

        if item_name == "config":
            continue

        if item_name == UPDATER_EXE_NAME.lower():
            continue

        destination = (
            target_folder
            / item.name
        )

        copy_item(
            item,
            destination,
        )

    installed_executable = (
        target_folder
        / APPLICATION_EXE_NAME
    )

    installed_internal = (
        target_folder
        / "_internal"
    )

    if not installed_executable.is_file():
        raise RuntimeError(
            "The updated application executable was not installed."
        )

    if not installed_internal.is_dir():
        raise RuntimeError(
            "The updated _internal folder was not installed."
        )

    logging.info(
        "New application files installed successfully."
    )


def restore_backup(
    target_folder: Path,
    backup_folder: Path,
) -> None:
    """Restore the previous application after a failed update."""

    logging.warning(
        "Restoring the previous application version."
    )

    clear_application_files(
        target_folder
    )

    for item in backup_folder.iterdir():
        destination = (
            target_folder
            / item.name
        )

        copy_item(
            item,
            destination,
        )

    logging.info(
        "Previous application version restored."
    )


def start_application(
    target_folder: Path,
) -> subprocess.Popen:
    """Start the updated application."""

    executable = (
        target_folder
        / APPLICATION_EXE_NAME
    )

    logging.info(
        "Starting updated application."
    )

    return subprocess.Popen(
        [str(executable)],
        cwd=str(
            target_folder
        ),
        creationflags=(
            subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.DETACHED_PROCESS
        ),
        close_fds=True,
    )


def confirm_application_started(
    process: subprocess.Popen,
    confirmation_seconds: int = 8,
) -> None:
    """Confirm the restarted application remains open briefly."""

    end_time = (
        time.monotonic()
        + confirmation_seconds
    )

    while time.monotonic() < end_time:
        return_code = process.poll()

        if return_code is not None:
            raise RuntimeError(
                "The updated application closed immediately "
                f"with exit code {return_code}."
            )

        time.sleep(
            1
        )

    logging.info(
        "The updated application remained running during "
        "the startup confirmation period."
    )


def schedule_workspace_cleanup(
    workspace: Path,
) -> None:
    """Delete temporary update files after the updater closes."""

    temporary_folder = Path(
        tempfile.gettempdir()
    )

    cleanup_script = (
        temporary_folder
        / f"aseat_update_cleanup_{os.getpid()}.cmd"
    )

    workspace_text = str(
        workspace.resolve()
    )

    script_text = (
        "@echo off\r\n"
        "timeout /t 4 /nobreak >nul\r\n"
        f'rmdir /s /q "{workspace_text}"\r\n'
        'del /f /q "%~f0"\r\n'
    )

    cleanup_script.write_text(
        script_text,
        encoding="utf-8",
    )

    subprocess.Popen(
        [
            "cmd.exe",
            "/c",
            "start",
            "",
            "/min",
            str(cleanup_script),
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
        close_fds=True,
    )

    logging.info(
        "Temporary update cleanup has been scheduled."
    )


def show_error_message(message: str) -> None:
    """Display an error without requiring the main application."""

    try:
        ctypes.windll.user32.MessageBoxW(
            0,
            message,
            "A-SEAT Update Failed",
            0x10,
        )
    except Exception:
        pass


def parse_arguments() -> argparse.Namespace:
    """Read updater command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Install an A-SEAT Audit Progress Extractor update."
        )
    )

    parser.add_argument(
        "--source",
        required=True,
        help="Extracted update payload folder.",
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Current application installation folder.",
    )

    parser.add_argument(
        "--workspace",
        required=True,
        help="Temporary update workspace.",
    )

    parser.add_argument(
        "--pid",
        required=True,
        type=int,
        help="Process ID of the running main application.",
    )

    parser.add_argument(
        "--version",
        required=True,
        help="Version being installed.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the external update installation."""

    arguments = parse_arguments()

    source_folder = Path(
        arguments.source
    ).resolve()

    target_folder = Path(
        arguments.target
    ).resolve()

    workspace = Path(
        arguments.workspace
    ).resolve()

    backup_folder = (
        workspace
        / "backup"
    )

    configure_logging(
        workspace
    )

    logging.info(
        "Starting installation of version %s.",
        arguments.version,
    )

    try:
        validate_paths(
            source_folder=source_folder,
            target_folder=target_folder,
            workspace=workspace,
        )

        wait_for_process_to_exit(
            process_id=arguments.pid
        )

        create_backup(
            target_folder=target_folder,
            backup_folder=backup_folder,
        )

        try:
            install_update(
                source_folder=source_folder,
                target_folder=target_folder,
            )

            updated_process = start_application(
                target_folder=target_folder
            )

            confirm_application_started(
                process=updated_process
            )

        except Exception:
            restore_backup(
                target_folder=target_folder,
                backup_folder=backup_folder,
            )

            try:
                start_application(
                    target_folder=target_folder
                )
            except Exception:
                logging.exception(
                    "The restored application could not be restarted."
                )

            raise

        logging.info(
            "Version %s installed successfully.",
            arguments.version,
        )

        schedule_workspace_cleanup(
            workspace
        )

        return 0

    except Exception as error:
        logging.exception(
            "The update installation failed."
        )

        show_error_message(
            "The application update could not be installed.\n\n"
            f"{error}\n\n"
            "The previous version has been retained where possible."
        )

        return 1


if __name__ == "__main__":
    sys.exit(
        main()
    )