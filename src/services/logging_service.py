import logging
import sys
import threading
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import Any

from PySide6.QtCore import QtMsgType, qInstallMessageHandler

from src.utils.app_paths import logs_folder
from src.utils.version import APP_NAME, APP_VERSION


class LoggingService:
    """Configure diagnostic logging for the application."""

    LOG_PREFIX = "aseat"
    RETENTION_DAYS = 7
    MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024
    BACKUP_FILES_PER_DAY = 1

    _configured = False
    _qt_handler_installed = False

    @classmethod
    def configure(cls) -> Path:
        """Configure logging and return today's log path."""

        folder = logs_folder()
        folder.mkdir(parents=True, exist_ok=True)
        cls._remove_expired_logs(folder)

        log_path = folder / f"{cls.LOG_PREFIX}_{datetime.now():%Y-%m-%d}.log"

        if cls._configured:
            return log_path

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.handlers.clear()

        handler = RotatingFileHandler(
            log_path,
            maxBytes=cls.MAX_FILE_SIZE_BYTES,
            backupCount=cls.BACKUP_FILES_PER_DAY,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root_logger.addHandler(handler)

        cls._install_exception_hooks()
        cls._install_qt_message_handler()
        cls._configured = True

        logger = logging.getLogger(__name__)
        logger.info("Application started | Version %s", APP_VERSION)

        return log_path

    @classmethod
    def shutdown(cls) -> None:
        """Flush and close logging handlers."""

        if cls._configured:
            logging.getLogger(__name__).info("Application closed.")

        logging.shutdown()
        cls._configured = False

    @classmethod
    def _install_exception_hooks(cls) -> None:
        """Capture unhandled exceptions in the main and worker threads."""

        original_hook = sys.excepthook

        def handle_exception(
            exception_type: type[BaseException],
            exception_value: BaseException,
            traceback_object: TracebackType | None,
        ) -> None:
            if issubclass(exception_type, KeyboardInterrupt):
                original_hook(
                    exception_type,
                    exception_value,
                    traceback_object,
                )
                return

            logging.getLogger("unhandled").critical(
                "Unhandled application exception.",
                exc_info=(
                    exception_type,
                    exception_value,
                    traceback_object,
                ),
            )

        sys.excepthook = handle_exception

        if hasattr(threading, "excepthook"):

            def handle_thread_exception(arguments: Any) -> None:
                logging.getLogger("unhandled.thread").critical(
                    "Unhandled exception in thread %s.",
                    getattr(arguments.thread, "name", "unknown"),
                    exc_info=(
                        arguments.exc_type,
                        arguments.exc_value,
                        arguments.exc_traceback,
                    ),
                )

            threading.excepthook = handle_thread_exception

    @classmethod
    def _install_qt_message_handler(cls) -> None:
        """Capture Qt warnings and critical messages."""

        if cls._qt_handler_installed:
            return

        def qt_message_handler(
            message_type: QtMsgType,
            context: Any,
            message: str,
        ) -> None:
            logger = logging.getLogger("qt")

            if message_type == QtMsgType.QtDebugMsg:
                logger.debug(message)
            elif message_type == QtMsgType.QtInfoMsg:
                logger.info(message)
            elif message_type == QtMsgType.QtWarningMsg:
                logger.warning(message)
            elif message_type == QtMsgType.QtCriticalMsg:
                logger.error(message)
            elif message_type == QtMsgType.QtFatalMsg:
                logger.critical(message)
            else:
                logger.info(message)

        qInstallMessageHandler(qt_message_handler)
        cls._qt_handler_installed = True

    @classmethod
    def _remove_expired_logs(cls, folder: Path) -> None:
        """Delete log files older than the retention period."""

        cutoff = (
            datetime.now()
            - timedelta(days=cls.RETENTION_DAYS)
        ).timestamp()

        for path in folder.glob(f"{cls.LOG_PREFIX}_*.log*"):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
            except OSError:
                continue
