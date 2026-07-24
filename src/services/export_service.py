from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl.styles import Alignment


class ExportService:
    """Exports extracted audit records to Excel and CSV."""

    DATE_COLUMNS = [
        "Planned Start Date",
        "Planned Completion Date",
    ]

    @staticmethod
    def _create_output_directory(
        base_folder: str,
    ) -> Path:
        output_directory = Path(base_folder).expanduser()

        if not output_directory.is_absolute():
            output_directory = output_directory.resolve()

        month_directory = (
            output_directory
            / datetime.now().strftime("%Y-%m")
        )

        month_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return month_directory

    @staticmethod
    def _create_filename(
        extension: str,
        audit_year: str = "",
    ) -> str:
        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        safe_year = "".join(
            character
            for character in audit_year
            if character.isdigit()
        )

        year_section = (
            f"_{safe_year}"
            if safe_year
            else ""
        )

        return (
            f"A-SEAT_Audit_Progress"
            f"{year_section}_{timestamp}.{extension}"
        )

    @staticmethod
    def _progress_heading() -> str:
        """Return the dated heading used for the progress column."""

        extraction_date = datetime.now().strftime(
            "%d %B %Y"
        )

        return (
            f"Progress to {extraction_date}"
        )

    @classmethod
    def _prepare_dataframe(
        cls,
        records: list[dict[str, Any]],
    ) -> pd.DataFrame:
        if not records:
            raise ValueError(
                "There are no extracted records to export."
            )

        dataframe = pd.DataFrame(records)

        expected_columns = [
            "Auditee Name",
            "Directorate",
            "Audit Name",
            "Audit Lead",
            "Audit Type",
            "Planned Start Date",
            "Planned Completion Date",
            "Audit Year",
            "Progress",
        ]

        for column in expected_columns:
            if column not in dataframe.columns:
                dataframe[column] = ""

        dataframe = dataframe[expected_columns]

        for date_column in cls.DATE_COLUMNS:
            dataframe[date_column] = pd.to_datetime(
                dataframe[date_column],
                errors="coerce",
            )

        dataframe = dataframe.rename(
            columns={
                "Progress": cls._progress_heading(),
            }
        )

        return dataframe

    def export_excel(
        self,
        records: list[dict[str, Any]],
        output_folder: str,
        audit_year: str = "",
    ) -> Path:
        """Export audit records to a formatted Excel workbook."""

        output_directory = self._create_output_directory(
            output_folder
        )

        output_path = (
            output_directory
            / self._create_filename(
                "xlsx",
                audit_year,
            )
        )

        dataframe = self._prepare_dataframe(
            records
        )

        progress_heading = self._progress_heading()

        with pd.ExcelWriter(
            output_path,
            engine="openpyxl",
            datetime_format="DD MMMM YYYY",
        ) as writer:
            dataframe.to_excel(
                writer,
                index=False,
                sheet_name="Audit Progress",
            )

            worksheet = writer.sheets[
                "Audit Progress"
            ]

            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = (
                worksheet.dimensions
            )

            header_map = {
                cell.value: cell.column
                for cell in worksheet[1]
            }

            for date_heading in self.DATE_COLUMNS:
                column_number = header_map.get(
                    date_heading
                )

                if column_number is None:
                    continue

                for row_number in range(
                    2,
                    worksheet.max_row + 1,
                ):
                    worksheet.cell(
                        row=row_number,
                        column=column_number,
                    ).number_format = (
                        "dd mmmm yyyy"
                    )

            progress_column = header_map.get(
                progress_heading
            )

            if progress_column is not None:
                for row_number in range(
                    2,
                    worksheet.max_row + 1,
                ):
                    cell = worksheet.cell(
                        row=row_number,
                        column=progress_column,
                    )

                    cell.alignment = Alignment(
                        vertical="top",
                        wrap_text=True,
                    )

                    if (
                        cell.value
                        and "\n" in str(cell.value)
                    ):
                        line_count = (
                            str(cell.value).count("\n")
                            + 1
                        )

                        worksheet.row_dimensions[
                            row_number
                        ].height = max(
                            15,
                            line_count * 15,
                        )

            for column_cells in worksheet.columns:
                maximum_length = 0

                column_letter = (
                    column_cells[0].column_letter
                )

                for cell in column_cells:
                    value_length = len(
                        str(cell.value or "")
                    )

                    maximum_length = max(
                        maximum_length,
                        value_length,
                    )

                worksheet.column_dimensions[
                    column_letter
                ].width = min(
                    max(
                        maximum_length + 3,
                        12,
                    ),
                    40,
                )

        return output_path

    def export_csv(
        self,
        records: list[dict[str, Any]],
        output_folder: str,
        audit_year: str = "",
    ) -> Path:
        """Export audit records to CSV."""

        output_directory = self._create_output_directory(
            output_folder
        )

        output_path = (
            output_directory
            / self._create_filename(
                "csv",
                audit_year,
            )
        )

        dataframe = self._prepare_dataframe(
            records
        )

        for date_column in self.DATE_COLUMNS:
            dataframe[date_column] = (
                dataframe[date_column]
                .dt.strftime("%d %B %Y")
                .fillna("")
            )

        dataframe.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
        )

        return output_path