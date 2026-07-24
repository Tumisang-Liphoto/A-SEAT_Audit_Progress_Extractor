import json
import re
from datetime import datetime
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
        "progressed": 0,
        "regressed": 1,
        "new": 2,
        "missing": 3,
        "unchanged": 4,
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
        }

        movement_values: list[float] = []

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
                    current_record
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

            comparison_rows.append(
                row
            )

        comparison_rows.sort(
            key=lambda row: (
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
            },
            "rows": [],
        }

    def _matched_audit_row(
        self,
        *,
        previous_record: dict[str, Any],
        current_record: dict[str, Any],
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

        previous_progress = (
            self._progress_numeric_value(
                previous_progress_text
            )
        )

        current_progress = (
            self._progress_numeric_value(
                current_progress_text
            )
        )

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
            != current_progress_text
        ):
            status = "progressed"
            movement_text = "Progress changed"

        row = self._display_record(
            current_record
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
                "movement_value": movement_value,
                "movement_text": movement_text,
            }
        )

        return row

    def _new_audit_row(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a comparison row for a newly identified audit."""

        row = self._display_record(
            record
        )

        row.update(
            {
                "status": "new",
                "status_label": "New audit",
                "previous_progress": "—",
                "current_progress": (
                    str(
                        record.get(
                            "Progress",
                            "",
                        )
                    ).strip()
                    or "Not set"
                ),
                "movement_value": None,
                "movement_text": "New audit",
            }
        )

        return row

    def _missing_audit_row(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a comparison row for an audit no longer present."""

        row = self._display_record(
            record
        )

        row.update(
            {
                "status": "missing",
                "status_label": "Missing audit",
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
                "movement_value": None,
                "movement_text": "Missing audit",
            }
        )

        return row

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
    def _progress_numeric_value(
        progress_text: str,
    ) -> float | None:
        """
        Convert progress text into one comparable number.

        Multi-year progress is represented by the average of the
        percentages shown for the audit.
        """

        percentages = [
            float(value)
            for value in re.findall(
                r"(\d+(?:\.\d+)?)\s*%",
                progress_text,
            )
        ]

        if not percentages:
            return None

        return sum(percentages) / len(
            percentages
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
            "missing": "Missing audit",
        }

        return labels.get(
            status,
            status.title(),
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