from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from src.core.audit_extractor import AuditExtractor
from src.services.export_service import ExportService


class ExtractionWorker(QObject):
    """Runs extraction and export outside the GUI thread."""

    progress_changed = Signal(int, str)
    extraction_completed = Signal(dict)
    extraction_failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        *,
        aseat_url: str,
        username: str,
        password: str,
        output_folder: str,
        output_format: str,
        audit_year: str,
        show_browser: bool,
    ) -> None:
        super().__init__()

        self.aseat_url = aseat_url
        self.username = username
        self.password = password
        self.output_folder = output_folder
        self.output_format = output_format
        self.audit_year = audit_year
        self.show_browser = show_browser

    def _report_progress(
        self,
        percentage: int,
        message: str,
    ) -> None:
        self.progress_changed.emit(
            percentage,
            message,
        )

    @Slot()
    def run(self) -> None:
        """Run extraction and export."""

        try:
            extractor = AuditExtractor(
                progress_callback=self._report_progress
            )

            records = extractor.extract(
                configured_url=self.aseat_url,
                username=self.username,
                password=self.password,
                show_browser=self.show_browser,
            )

            # Remove the password as soon as authentication is complete.
            self.password = ""

            self._report_progress(
                85,
                "Preparing output files",
            )

            export_service = ExportService()
            output_paths: list[Path] = []

            if self.output_format in {
                "Excel Workbook",
                "Excel and CSV",
            }:
                self._report_progress(
                    90,
                    "Creating Excel workbook",
                )

                excel_path = export_service.export_excel(
                    records=records,
                    output_folder=self.output_folder,
                    audit_year=self.audit_year,
                )

                output_paths.append(excel_path)

            if self.output_format in {
                "CSV File",
                "Excel and CSV",
            }:
                self._report_progress(
                    95,
                    "Creating CSV file",
                )

                csv_path = export_service.export_csv(
                    records=records,
                    output_folder=self.output_folder,
                    audit_year=self.audit_year,
                )

                output_paths.append(csv_path)

            if not output_paths:
                raise RuntimeError(
                    "No output format was selected."
                )

            self._report_progress(
                100,
                "Extraction completed",
            )

            result: dict[str, Any] = {
                "record_count": len(records),
                "output_paths": [
                    str(path)
                    for path in output_paths
                ],
            }

            self.extraction_completed.emit(result)

        except Exception as error:
            self.password = ""
            self.extraction_failed.emit(str(error))

        finally:
            self.username = ""
            self.password = ""
            self.finished.emit()