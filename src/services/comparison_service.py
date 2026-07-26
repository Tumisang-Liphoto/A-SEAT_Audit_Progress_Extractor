import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.app_paths import config_folder


class ComparisonService:
    """
    Saves extraction snapshots and compares the two most recent
    successful extractions.
    """

    SNAPSHOT_FOLDER_NAME = "extraction_history"

    MATCH_FIELDS = (
        "Auditee Name",
        "Audit Name",
        "Audit Type",
        "Audit Year",
    )

    DISPLAY_FIELDS = (
        "Auditee Name",
        "Directorate",
        "Audit Name",
        "Audit Lead",
        "Audit Type",
        "Planned Start Date",
        "Planned Completion Date",
        "Audit Year",
    )

    STATUS_ORDER = {
        "regressed": 0,
        "not_comparable": 1,
        "progressed": 2,
        "new": 3,
        "missing": 4,
        "unchanged": 5,
    }

    DELIVERY_STATUS_ORDER = {
        "progress_year_mismatch": 0,
        "missing_progress": 1,
        "invalid_progress": 2,
        "overdue": 3,
        "not_started_late": 4,
        "due_soon": 5,
        "in_progress": 6,
        "not_yet_started": 7,
        "completed": 8,
        "missing_dates": 9,
        "invalid_dates": 10,
        "not_currently_listed": 11,
    }

    def __init__(self) -> None:
        self.history_folder = (
            config_folder()
            / self.SNAPSHOT_FOLDER_NAME
        )

    def save_snapshot(
        self,
        records: list[dict[str, Any]],
        extracted_at: datetime | None = None,
    ) -> Path:
        """Save one successful extraction as a JSON snapshot."""

        if not records:
            raise ValueError(
                "An empty extraction cannot be saved as a snapshot."
            )

        snapshot_time = extracted_at or datetime.now()

        self.history_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = snapshot_time.strftime(
            "%Y-%m-%d_%H-%M-%S_%f"
        )

        snapshot_path = (
            self.history_folder
            / f"extraction_{timestamp}.json"
        )

        snapshot_data = {
            "extracted_at": snapshot_time.isoformat(
                timespec="seconds"
            ),
            "record_count": len(records),
            "records": [
                self._clean_record(record)
                for record in records
            ],
        }

        temporary_path = snapshot_path.with_suffix(
            ".json.tmp"
        )

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                snapshot_data,
                file,
                indent=4,
                ensure_ascii=False,
            )

        temporary_path.replace(
            snapshot_path
        )

        return snapshot_path

    def list_snapshots(self) -> list[Path]:
        """Return available snapshots from oldest to newest."""

        if not self.history_folder.exists():
            return []

        snapshots = [
            path
            for path in self.history_folder.glob(
                "extraction_*.json"
            )
            if path.is_file()
        ]

        return sorted(
            snapshots,
            key=lambda path: path.name,
        )

    def compare_latest_snapshots(
        self,
    ) -> dict[str, Any]:
        """Compare the two most recent extraction snapshots."""

        snapshots = self.list_snapshots()

        if len(snapshots) < 2:
            return self.empty_comparison()

        previous_snapshot = self._load_snapshot(
            snapshots[-2]
        )

        current_snapshot = self._load_snapshot(
            snapshots[-1]
        )

        return self.compare_snapshots(
            previous_snapshot=previous_snapshot,
            current_snapshot=current_snapshot,
        )

    def compare_snapshots(
        self,
        *,
        previous_snapshot: dict[str, Any],
        current_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """Compare two loaded snapshots."""

        previous_records = self._records_by_key(
            previous_snapshot.get(
                "records",
                [],
            )
        )

        current_records = self._records_by_key(
            current_snapshot.get(
                "records",
                [],
            )
        )

        all_keys = sorted(
            set(previous_records)
            | set(current_records)
        )

        comparison_rows: list[dict[str, Any]] = []

        totals = {
            "audits_compared": 0,
            "progressed": 0,
            "unchanged": 0,
            "regressed": 0,
            "new": 0,
            "missing": 0,
            "not_comparable": 0,
        }

        delivery_totals = {
            "completed": 0,
            "overdue": 0,
            "due_soon": 0,
            "not_started_late": 0,
            "in_progress": 0,
            "not_yet_started": 0,
            "missing_progress": 0,
            "invalid_progress": 0,
            "progress_year_mismatch": 0,
            "missing_dates": 0,
            "invalid_dates": 0,
            "not_currently_listed": 0,
        }

        movement_values: list[float] = []

        assessment_date = self._snapshot_date(
            str(
                current_snapshot.get(
                    "extracted_at",
                    "",
                )
            )
        )

        for audit_key in all_keys:
            previous_record = previous_records.get(
                audit_key
            )

            current_record = current_records.get(
                audit_key
            )

            if (
                previous_record is None
                and current_record is not None
            ):
                row = self._new_audit_row(
                    current_record,
                    assessment_date=assessment_date,
                )

                totals["new"] += 1

            elif (
                previous_record is not None
                and current_record is None
            ):
                row = self._missing_audit_row(
                    previous_record
                )

                totals["missing"] += 1

            elif (
                previous_record is not None
                and current_record is not None
            ):
                row = self._matched_audit_row(
                    previous_record=previous_record,
                    current_record=current_record,
                    assessment_date=assessment_date,
                )

                totals["audits_compared"] += 1
                totals[row["status"]] += 1

                movement = row.get(
                    "movement_value"
                )

                if isinstance(
                    movement,
                    (int, float),
                ):
                    movement_values.append(
                        float(movement)
                    )
            else:
                continue

            delivery_status = str(
                row.get(
                    "delivery_status",
                    "",
                )
            )

            if delivery_status in delivery_totals:
                delivery_totals[
                    delivery_status
                ] += 1

            comparison_rows.append(
                row
            )

        comparison_rows.sort(
            key=lambda row: (
                self.DELIVERY_STATUS_ORDER.get(
                    str(
                        row.get(
                            "delivery_status",
                            "",
                        )
                    ),
                    99,
                ),
                self.STATUS_ORDER.get(
                    str(
                        row.get(
                            "status",
                            "",
                        )
                    ),
                    99,
                ),
                self._normalise_text(
                    row.get(
                        "Auditee Name",
                        "",
                    )
                ),
                self._normalise_text(
                    row.get(
                        "Audit Name",
                        "",
                    )
                ),
            )
        )

        average_movement = (
            sum(movement_values)
            / len(movement_values)
            if movement_values
            else 0.0
        )

        previous_extracted_at = str(
            previous_snapshot.get(
                "extracted_at",
                "",
            )
        )

        current_extracted_at = str(
            current_snapshot.get(
                "extracted_at",
                "",
            )
        )

        return {
            "has_comparison": True,
            "previous_extracted_at": (
                previous_extracted_at
            ),
            "current_extracted_at": (
                current_extracted_at
            ),
            "previous_display_date": (
                self._format_snapshot_date(
                    previous_extracted_at
                )
            ),
            "current_display_date": (
                self._format_snapshot_date(
                    current_extracted_at
                )
            ),
            "previous_record_count": int(
                previous_snapshot.get(
                    "record_count",
                    len(previous_records),
                )
            ),
            "assessment_date": assessment_date.isoformat(),
            "assessment_display_date": assessment_date.strftime(
                "%d %B %Y"
            ),
            "current_record_count": int(
                current_snapshot.get(
                    "record_count",
                    len(current_records),
                )
            ),
            "average_movement": round(
                average_movement,
                1,
            ),
            "summary": totals,
            "delivery_summary": delivery_totals,
            "rows": comparison_rows,
        }

    @staticmethod
    def empty_comparison() -> dict[str, Any]:
        """Return the state used before two snapshots exist."""

        return {
            "has_comparison": False,
            "previous_extracted_at": "",
            "current_extracted_at": "",
            "previous_display_date": "",
            "current_display_date": "",
            "assessment_date": "",
            "assessment_display_date": "",
            "previous_record_count": 0,
            "current_record_count": 0,
            "average_movement": 0.0,
            "summary": {
                "audits_compared": 0,
                "progressed": 0,
                "unchanged": 0,
                "regressed": 0,
                "new": 0,
                "missing": 0,
                "not_comparable": 0,
            },
            "delivery_summary": {
                "completed": 0,
                "overdue": 0,
                "due_soon": 0,
                "not_started_late": 0,
                "in_progress": 0,
                "not_yet_started": 0,
                "missing_progress": 0,
                "invalid_progress": 0,
                "progress_year_mismatch": 0,
                "missing_dates": 0,
                "invalid_dates": 0,
                "not_currently_listed": 0,
            },
            "rows": [],
        }

    def _matched_audit_row(
        self,
        *,
        previous_record: dict[str, Any],
        current_record: dict[str, Any],
        assessment_date: date,
    ) -> dict[str, Any]:
        """Build a comparison row for an audit in both snapshots."""

        previous_progress_text = str(
            previous_record.get(
                "Progress",
                "",
            )
        ).strip()

        current_progress_text = str(
            current_record.get(
                "Progress",
                "",
            )
        ).strip()

        previous_result = self._parse_progress(
            progress_text=previous_progress_text,
            audit_year=str(
                previous_record.get(
                    "Audit Year",
                    "",
                )
            ),
        )

        current_result = self._parse_progress(
            progress_text=current_progress_text,
            audit_year=str(
                current_record.get(
                    "Audit Year",
                    "",
                )
            ),
        )

        previous_progress = previous_result["value"]
        current_progress = current_result["value"]

        movement_value: float | None = None
        status = "unchanged"
        movement_text = "No change"

        if (
            previous_progress is not None
            and current_progress is not None
        ):
            movement_value = round(
                current_progress
                - previous_progress,
                1,
            )

            if movement_value > 0:
                status = "progressed"
                movement_text = (
                    f"+{self._format_number(movement_value)} "
                    "points"
                )
            elif movement_value < 0:
                status = "regressed"
                movement_text = (
                    f"{self._format_number(movement_value)} "
                    "points"
                )
        elif (
            previous_progress_text
            == current_progress_text
            and previous_result["status"]
            == current_result["status"]
        ):
            status = "not_comparable"
            movement_text = "Not comparable"
        elif previous_progress_text != current_progress_text:
            status = "not_comparable"
            movement_text = (
                "Progress changed but is not comparable"
            )

        row = self._display_record(
            current_record
        )

        delivery = self._delivery_assessment(
            record=current_record,
            progress_result=current_result,
            assessment_date=assessment_date,
        )

        row.update(
            {
                "status": status,
                "status_label": (
                    self._status_label(status)
                ),
                "previous_progress": (
                    previous_progress_text
                    or "Not set"
                ),
                "current_progress": (
                    current_progress_text
                    or "Not set"
                ),
                "previous_progress_value": previous_progress,
                "current_progress_value": current_progress,
                "previous_progress_status": previous_result["status"],
                "current_progress_status": current_result["status"],
                "movement_value": movement_value,
                "movement_text": movement_text,
                **delivery,
            }
        )

        return row

    def _new_audit_row(
        self,
        record: dict[str, Any],
        *,
        assessment_date: date,
    ) -> dict[str, Any]:
        """Build a comparison row for a newly identified audit."""

        progress_text = str(
            record.get(
                "Progress",
                "",
            )
        ).strip()

        progress_result = self._parse_progress(
            progress_text=progress_text,
            audit_year=str(
                record.get(
                    "Audit Year",
                    "",
                )
            ),
        )

        row = self._display_record(
            record
        )

        row.update(
            {
                "status": "new",
                "status_label": "New audit",
                "previous_progress": "—",
                "current_progress": progress_text or "Not set",
                "previous_progress_value": None,
                "current_progress_value": progress_result["value"],
                "previous_progress_status": "not_available",
                "current_progress_status": progress_result["status"],
                "movement_value": None,
                "movement_text": "New audit",
                **self._delivery_assessment(
                    record=record,
                    progress_result=progress_result,
                    assessment_date=assessment_date,
                ),
            }
        )

        return row

    def _missing_audit_row(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a row for an audit no longer present."""

        row = self._display_record(
            record
        )

        row.update(
            {
                "status": "missing",
                "status_label": "No longer listed",
                "previous_progress": (
                    str(
                        record.get(
                            "Progress",
                            "",
                        )
                    ).strip()
                    or "Not set"
                ),
                "current_progress": "—",
                "previous_progress_value": None,
                "current_progress_value": None,
                "previous_progress_status": "not_available",
                "current_progress_status": "not_available",
                "movement_value": None,
                "movement_text": "No longer listed",
                "delivery_status": "not_currently_listed",
                "delivery_status_label": "Not currently listed",
                "delivery_issue": "",
                "days_to_completion": None,
                "planned_start_date_value": "",
                "planned_completion_date_value": "",
            }
        )

        return row

    def _delivery_assessment(
        self,
        *,
        record: dict[str, Any],
        progress_result: dict[str, Any],
        assessment_date: date,
    ) -> dict[str, Any]:
        """Assess current delivery status."""

        progress_status = str(
            progress_result.get(
                "status",
                "",
            )
        )
        progress_value = progress_result.get(
            "value"
        )

        start_date, start_status = self._parse_date(
            str(
                record.get(
                    "Planned Start Date",
                    "",
                )
            )
        )
        completion_date, completion_status = self._parse_date(
            str(
                record.get(
                    "Planned Completion Date",
                    "",
                )
            )
        )

        days_to_completion = (
            (
                completion_date
                - assessment_date
            ).days
            if completion_date is not None
            else None
        )

        if progress_status == "progress_year_mismatch":
            return self._delivery_result(
                "progress_year_mismatch",
                str(
                    progress_result.get(
                        "message",
                        "",
                    )
                ),
                start_date,
                completion_date,
                days_to_completion,
            )

        if progress_status == "missing_progress":
            return self._delivery_result(
                "missing_progress",
                "No usable progress percentage is available.",
                start_date,
                completion_date,
                days_to_completion,
            )

        if progress_status == "invalid_progress":
            return self._delivery_result(
                "invalid_progress",
                "The progress value could not be interpreted.",
                start_date,
                completion_date,
                days_to_completion,
            )

        if isinstance(
            progress_value,
            (int, float),
        ) and progress_value >= 100:
            return self._delivery_result(
                "completed",
                "",
                start_date,
                completion_date,
                days_to_completion,
            )

        if (
            start_status == "invalid"
            or completion_status == "invalid"
        ):
            return self._delivery_result(
                "invalid_dates",
                "One or more planned dates could not be interpreted.",
                start_date,
                completion_date,
                days_to_completion,
            )

        if (
            start_status == "missing"
            or completion_status == "missing"
        ):
            return self._delivery_result(
                "missing_dates",
                "One or more planned dates are missing.",
                start_date,
                completion_date,
                days_to_completion,
            )

        if (
            completion_date is not None
            and completion_date < assessment_date
        ):
            return self._delivery_result(
                "overdue",
                (
                    "Planned completion date passed "
                    f"{abs(days_to_completion or 0)} day(s) ago."
                ),
                start_date,
                completion_date,
                days_to_completion,
            )

        if (
            start_date is not None
            and start_date < assessment_date
            and float(progress_value or 0) <= 0
        ):
            return self._delivery_result(
                "not_started_late",
                (
                    "Planned start date has passed but "
                    "progress remains 0%."
                ),
                start_date,
                completion_date,
                days_to_completion,
            )

        if (
            completion_date is not None
            and 0 <= (
                completion_date
                - assessment_date
            ).days <= 30
        ):
            return self._delivery_result(
                "due_soon",
                (
                    "Planned completion is in "
                    f"{days_to_completion} day(s)."
                ),
                start_date,
                completion_date,
                days_to_completion,
            )

        if (
            start_date is not None
            and start_date > assessment_date
        ):
            return self._delivery_result(
                "not_yet_started",
                "Planned start date is in the future.",
                start_date,
                completion_date,
                days_to_completion,
            )

        return self._delivery_result(
            "in_progress",
            "",
            start_date,
            completion_date,
            days_to_completion,
        )

    @classmethod
    def _delivery_result(
        cls,
        status: str,
        issue: str,
        start_date: date | None,
        completion_date: date | None,
        days_to_completion: int | None,
    ) -> dict[str, Any]:
        """Return a consistent delivery result."""

        return {
            "delivery_status": status,
            "delivery_status_label": (
                cls._delivery_status_label(
                    status
                )
            ),
            "delivery_issue": issue,
            "days_to_completion": days_to_completion,
            "planned_start_date_value": (
                start_date.isoformat()
                if start_date is not None
                else ""
            ),
            "planned_completion_date_value": (
                completion_date.isoformat()
                if completion_date is not None
                else ""
            ),
        }

    @staticmethod
    def _parse_progress(
        *,
        progress_text: str,
        audit_year: str,
    ) -> dict[str, Any]:
        """Parse progress without averaging across years."""

        clean_text = progress_text.strip()
        clean_audit_year = audit_year.strip()

        if not clean_text:
            return {
                "status": "missing_progress",
                "value": None,
                "matched_year": "",
                "message": "Progress is not set.",
            }

        year_pairs = re.findall(
            r"\b(20\d{2})\s*:\s*"
            r"(\d+(?:\.\d+)?)\s*%",
            clean_text,
        )

        if year_pairs:
            year_values = {
                year: float(value)
                for year, value in year_pairs
            }

            audit_years = re.findall(
                r"\b20\d{2}\b",
                clean_audit_year,
            )

            for year in audit_years:
                if year in year_values:
                    return {
                        "status": "valid",
                        "value": year_values[year],
                        "matched_year": year,
                        "message": "",
                    }

            if len(year_values) == 1 and not audit_years:
                year, value = next(
                    iter(
                        year_values.items()
                    )
                )
                return {
                    "status": "valid",
                    "value": value,
                    "matched_year": year,
                    "message": "",
                }

            return {
                "status": "progress_year_mismatch",
                "value": None,
                "matched_year": "",
                "message": (
                    "Progress year(s) "
                    f"{', '.join(year_values)} do not match "
                    f"Audit Year {clean_audit_year or 'not set'}."
                ),
            }

        percentages = re.findall(
            r"(\d+(?:\.\d+)?)\s*%",
            clean_text,
        )

        if len(percentages) == 1:
            return {
                "status": "valid",
                "value": float(
                    percentages[0]
                ),
                "matched_year": "",
                "message": "",
            }

        if len(percentages) > 1:
            return {
                "status": "invalid_progress",
                "value": None,
                "matched_year": "",
                "message": (
                    "Multiple percentages were found without "
                    "year labels."
                ),
            }

        return {
            "status": "invalid_progress",
            "value": None,
            "matched_year": "",
            "message": (
                "No percentage could be interpreted."
            ),
        }

    @staticmethod
    def _parse_date(
        value: str,
    ) -> tuple[date | None, str]:
        """Parse common A-SEAT date formats."""

        clean_value = value.strip()

        if not clean_value:
            return None, "missing"

        for format_string in (
            "%Y-%m-%d",
            "%d %B %Y",
            "%d %b %Y",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ):
            try:
                return (
                    datetime.strptime(
                        clean_value,
                        format_string,
                    ).date(),
                    "valid",
                )
            except ValueError:
                continue

        try:
            return (
                datetime.fromisoformat(
                    clean_value
                ).date(),
                "valid",
            )
        except ValueError:
            return None, "invalid"

    @staticmethod
    def _snapshot_date(
        iso_value: str,
    ) -> date:
        """Return the extraction date used for assessment."""

        try:
            return datetime.fromisoformat(
                iso_value
            ).date()
        except ValueError:
            return date.today()

    def _records_by_key(
        self,
        records: Any,
    ) -> dict[tuple[str, ...], dict[str, Any]]:
        """Index records using the stable comparison fields."""

        if not isinstance(
            records,
            list,
        ):
            return {}

        indexed_records: dict[
            tuple[str, ...],
            dict[str, Any],
        ] = {}

        duplicate_counts: dict[
            tuple[str, ...],
            int,
        ] = {}

        for raw_record in records:
            if not isinstance(
                raw_record,
                dict,
            ):
                continue

            record = self._clean_record(
                raw_record
            )

            base_key = tuple(
                self._normalise_text(
                    record.get(
                        field,
                        "",
                    )
                )
                for field in self.MATCH_FIELDS
            )

            duplicate_number = (
                duplicate_counts.get(
                    base_key,
                    0,
                )
            )

            duplicate_counts[
                base_key
            ] = duplicate_number + 1

            comparison_key = (
                *base_key,
                str(duplicate_number),
            )

            indexed_records[
                comparison_key
            ] = record

        return indexed_records

    @classmethod
    def _clean_record(
        cls,
        record: dict[str, Any],
    ) -> dict[str, str]:
        """Convert record values into safe serialisable strings."""

        fields = {
            *cls.DISPLAY_FIELDS,
            "Progress",
        }

        return {
            field: str(
                record.get(
                    field,
                    "",
                )
                or ""
            ).strip()
            for field in fields
        }

    @classmethod
    def _display_record(
        cls,
        record: dict[str, Any],
    ) -> dict[str, str]:
        """Return fields displayed by the dashboard table."""

        return {
            field: str(
                record.get(
                    field,
                    "",
                )
                or ""
            ).strip()
            for field in cls.DISPLAY_FIELDS
        }

    @staticmethod
    def _normalise_text(
        value: Any,
    ) -> str:
        """Normalise text for matching and sorting."""

        return re.sub(
            r"\s+",
            " ",
            str(value or "")
            .strip()
            .lower(),
        )

    @staticmethod
    def _format_number(
        value: float,
    ) -> str:
        """Format a movement value without unnecessary decimals."""

        if value.is_integer():
            return str(
                int(value)
            )

        return f"{value:.1f}"

    @staticmethod
    def _status_label(
        status: str,
    ) -> str:
        labels = {
            "progressed": "Progressed",
            "unchanged": "No change",
            "regressed": "Regressed",
            "new": "New audit",
            "missing": "No longer listed",
            "not_comparable": "Not comparable",
        }

        return labels.get(
            status,
            status.title(),
        )

    @staticmethod
    def _delivery_status_label(
        status: str,
    ) -> str:
        labels = {
            "completed": "Completed",
            "overdue": "Overdue",
            "due_soon": "Due soon",
            "not_started_late": "Not started late",
            "in_progress": "In progress",
            "not_yet_started": "Not yet started",
            "missing_progress": "Missing progress",
            "invalid_progress": "Invalid progress",
            "progress_year_mismatch": "Progress-year mismatch",
            "missing_dates": "Missing dates",
            "invalid_dates": "Invalid dates",
            "not_currently_listed": "Not currently listed",
        }

        return labels.get(
            status,
            status.replace(
                "_",
                " ",
            ).title(),
        )

    @staticmethod
    def _format_snapshot_date(
        iso_value: str,
    ) -> str:
        """Format an ISO snapshot date for the dashboard."""

        if not iso_value:
            return ""

        try:
            parsed_date = datetime.fromisoformat(
                iso_value
            )

            return parsed_date.strftime(
                "%d %B %Y, %H:%M"
            )

        except ValueError:
            return iso_value

    @staticmethod
    def _load_snapshot(
        snapshot_path: Path,
    ) -> dict[str, Any]:
        """Load and validate a JSON extraction snapshot."""

        try:
            with snapshot_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                snapshot = json.load(
                    file
                )

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(
                (
                    "The extraction snapshot could not "
                    f"be read: {snapshot_path.name}"
                )
            ) from error

        if not isinstance(
            snapshot,
            dict,
        ):
            raise RuntimeError(
                (
                    "The extraction snapshot is invalid: "
                    f"{snapshot_path.name}"
                )
            )

        records = snapshot.get(
            "records"
        )

        if not isinstance(
            records,
            list,
        ):
            raise RuntimeError(
                (
                    "The extraction snapshot does not contain "
                    f"a valid record list: {snapshot_path.name}"
                )
            )

        return snapshot