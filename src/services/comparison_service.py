import json
import re
import unicodedata
from difflib import SequenceMatcher
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

    EXACT_IDENTITY_FIELDS = (
        "Auditee Name",
        "Audit Name",
        "Audit Type",
        "Audit Year",
    )

    FUZZY_SCOPE_FIELDS = (
        "Audit Type",
        "Audit Year",
    )

    FUZZY_MATCH_THRESHOLD = 0.88
    FUZZY_MATCH_MARGIN = 0.08

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
        """Compare two loaded snapshots using staged record matching."""

        previous_records = self._clean_record_list(
            previous_snapshot.get(
                "records",
                [],
            )
        )

        current_records = self._clean_record_list(
            current_snapshot.get(
                "records",
                [],
            )
        )

        (
            matched_records,
            unmatched_previous,
            unmatched_current,
        ) = self._match_records(
            previous_records=previous_records,
            current_records=current_records,
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

        matching_totals = {
            "exact": 0,
            "strong_identity": 0,
            "fuzzy": 0,
            "new": len(
                unmatched_current
            ),
            "missing": len(
                unmatched_previous
            ),
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

        for (
            previous_record,
            current_record,
            match_information,
        ) in matched_records:
            row = self._matched_audit_row(
                previous_record=previous_record,
                current_record=current_record,
                assessment_date=assessment_date,
            )

            row.update(
                match_information
            )

            totals["audits_compared"] += 1
            totals[row["status"]] += 1

            match_method = str(
                match_information.get(
                    "match_method",
                    "",
                )
            )

            if match_method in matching_totals:
                matching_totals[
                    match_method
                ] += 1

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

            comparison_rows.append(
                row
            )

        for current_record in unmatched_current:
            row = self._new_audit_row(
                current_record,
                assessment_date=assessment_date,
            )

            row.update(
                {
                    "match_method": "new",
                    "match_method_label": "New audit",
                    "match_score": None,
                    "identity_changed": False,
                    "identity_change_text": "",
                }
            )

            totals["new"] += 1
            comparison_rows.append(
                row
            )

        for previous_record in unmatched_previous:
            row = self._missing_audit_row(
                previous_record
            )

            row.update(
                {
                    "match_method": "missing",
                    "match_method_label": "No match found",
                    "match_score": None,
                    "identity_changed": False,
                    "identity_change_text": "",
                }
            )

            totals["missing"] += 1
            comparison_rows.append(
                row
            )

        for row in comparison_rows:
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
            "assessment_date": assessment_date.isoformat(),
            "assessment_display_date": assessment_date.strftime(
                "%d %B %Y"
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
            "delivery_summary": delivery_totals,
            "matching_summary": matching_totals,
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
            "matching_summary": {
                "exact": 0,
                "strong_identity": 0,
                "fuzzy": 0,
                "new": 0,
                "missing": 0,
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

    def _clean_record_list(
        self,
        records: Any,
    ) -> list[dict[str, str]]:
        """Return a clean list while preserving duplicate records."""

        if not isinstance(
            records,
            list,
        ):
            return []

        return [
            self._clean_record(
                record
            )
            for record in records
            if isinstance(
                record,
                dict,
            )
        ]

    def _match_records(
        self,
        *,
        previous_records: list[dict[str, str]],
        current_records: list[dict[str, str]],
    ) -> tuple[
        list[
            tuple[
                dict[str, str],
                dict[str, str],
                dict[str, Any],
            ]
        ],
        list[dict[str, str]],
        list[dict[str, str]],
    ]:
        """
        Match records in three conservative stages.

        Stage 1 uses the full stable identity.
        Stage 2 accepts the same audit name, type and year where only
        the auditee wording changed.
        Stage 3 uses fuzzy name matching within the same type and year,
        but only where the best score is strong and unambiguous.
        """

        unmatched_previous = set(
            range(
                len(previous_records)
            )
        )

        unmatched_current = set(
            range(
                len(current_records)
            )
        )

        matches: list[
            tuple[
                dict[str, str],
                dict[str, str],
                dict[str, Any],
            ]
        ] = []

        exact_candidates: dict[
            tuple[str, ...],
            list[int],
        ] = {}

        for current_index, record in enumerate(
            current_records
        ):
            key = self._identity_key(
                record,
                self.EXACT_IDENTITY_FIELDS,
            )

            exact_candidates.setdefault(
                key,
                [],
            ).append(
                current_index
            )

        for previous_index, previous_record in enumerate(
            previous_records
        ):
            key = self._identity_key(
                previous_record,
                self.EXACT_IDENTITY_FIELDS,
            )

            candidate_indexes = exact_candidates.get(
                key,
                [],
            )

            current_index = next(
                (
                    index
                    for index in candidate_indexes
                    if index in unmatched_current
                ),
                None,
            )

            if current_index is None:
                continue

            unmatched_previous.discard(
                previous_index
            )
            unmatched_current.discard(
                current_index
            )

            matches.append(
                (
                    previous_record,
                    current_records[
                        current_index
                    ],
                    self._match_information(
                        previous_record=previous_record,
                        current_record=current_records[
                            current_index
                        ],
                        method="exact",
                        score=1.0,
                    ),
                )
            )

        for previous_index in sorted(
            tuple(
                unmatched_previous
            )
        ):
            previous_record = previous_records[
                previous_index
            ]

            candidates = [
                current_index
                for current_index in unmatched_current
                if (
                    self._normalise_text(
                        current_records[
                            current_index
                        ].get(
                            "Audit Name",
                            "",
                        )
                    )
                    == self._normalise_text(
                        previous_record.get(
                            "Audit Name",
                            "",
                        )
                    )
                    and self._same_scope(
                        previous_record,
                        current_records[
                            current_index
                        ],
                    )
                )
            ]

            if len(candidates) != 1:
                continue

            current_index = candidates[0]

            unmatched_previous.discard(
                previous_index
            )
            unmatched_current.discard(
                current_index
            )

            matches.append(
                (
                    previous_record,
                    current_records[
                        current_index
                    ],
                    self._match_information(
                        previous_record=previous_record,
                        current_record=current_records[
                            current_index
                        ],
                        method="strong_identity",
                        score=1.0,
                    ),
                )
            )

        possible_matches: list[
            tuple[
                float,
                float,
                int,
                int,
            ]
        ] = []

        for previous_index in unmatched_previous:
            previous_record = previous_records[
                previous_index
            ]

            scored_candidates: list[
                tuple[
                    float,
                    int,
                ]
            ] = []

            for current_index in unmatched_current:
                current_record = current_records[
                    current_index
                ]

                if not self._same_scope(
                    previous_record,
                    current_record,
                ):
                    continue

                score = self._record_similarity(
                    previous_record,
                    current_record,
                )

                scored_candidates.append(
                    (
                        score,
                        current_index,
                    )
                )

            scored_candidates.sort(
                reverse=True
            )

            if not scored_candidates:
                continue

            best_score, best_current = (
                scored_candidates[0]
            )

            second_score = (
                scored_candidates[1][0]
                if len(
                    scored_candidates
                ) > 1
                else 0.0
            )

            if (
                best_score
                >= self.FUZZY_MATCH_THRESHOLD
                and (
                    best_score
                    - second_score
                )
                >= self.FUZZY_MATCH_MARGIN
            ):
                possible_matches.append(
                    (
                        best_score,
                        second_score,
                        previous_index,
                        best_current,
                    )
                )

        possible_matches.sort(
            reverse=True
        )

        for (
            best_score,
            _,
            previous_index,
            current_index,
        ) in possible_matches:
            if (
                previous_index
                not in unmatched_previous
                or current_index
                not in unmatched_current
            ):
                continue

            previous_record = previous_records[
                previous_index
            ]

            current_record = current_records[
                current_index
            ]

            unmatched_previous.discard(
                previous_index
            )
            unmatched_current.discard(
                current_index
            )

            matches.append(
                (
                    previous_record,
                    current_record,
                    self._match_information(
                        previous_record=previous_record,
                        current_record=current_record,
                        method="fuzzy",
                        score=best_score,
                    ),
                )
            )

        return (
            matches,
            [
                previous_records[index]
                for index in sorted(
                    unmatched_previous
                )
            ],
            [
                current_records[index]
                for index in sorted(
                    unmatched_current
                )
            ],
        )

    @classmethod
    def _identity_key(
        cls,
        record: dict[str, Any],
        fields: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Build a normalised identity key."""

        return tuple(
            cls._normalise_text(
                record.get(
                    field,
                    "",
                )
            )
            for field in fields
        )

    @classmethod
    def _same_scope(
        cls,
        previous_record: dict[str, Any],
        current_record: dict[str, Any],
    ) -> bool:
        """Require the same audit type and year for fuzzy matching."""

        return cls._identity_key(
            previous_record,
            cls.FUZZY_SCOPE_FIELDS,
        ) == cls._identity_key(
            current_record,
            cls.FUZZY_SCOPE_FIELDS,
        )

    @classmethod
    def _record_similarity(
        cls,
        previous_record: dict[str, Any],
        current_record: dict[str, Any],
    ) -> float:
        """Calculate a conservative weighted identity similarity."""

        previous_auditee = cls._normalise_text(
            previous_record.get(
                "Auditee Name",
                "",
            )
        )
        current_auditee = cls._normalise_text(
            current_record.get(
                "Auditee Name",
                "",
            )
        )
        previous_audit = cls._normalise_text(
            previous_record.get(
                "Audit Name",
                "",
            )
        )
        current_audit = cls._normalise_text(
            current_record.get(
                "Audit Name",
                "",
            )
        )

        auditee_score = SequenceMatcher(
            None,
            previous_auditee,
            current_auditee,
        ).ratio()

        audit_score = SequenceMatcher(
            None,
            previous_audit,
            current_audit,
        ).ratio()

        if not previous_auditee or not current_auditee:
            auditee_score = 0.0

        if not previous_audit or not current_audit:
            audit_score = 0.0

        return round(
            (
                auditee_score
                * 0.45
            )
            + (
                audit_score
                * 0.55
            ),
            4,
        )

    @classmethod
    def _match_information(
        cls,
        *,
        previous_record: dict[str, Any],
        current_record: dict[str, Any],
        method: str,
        score: float,
    ) -> dict[str, Any]:
        """Describe how two records were matched."""

        changed_fields = []

        for field in (
            "Auditee Name",
            "Audit Name",
        ):
            previous_value = str(
                previous_record.get(
                    field,
                    "",
                )
            ).strip()

            current_value = str(
                current_record.get(
                    field,
                    "",
                )
            ).strip()

            if (
                cls._normalise_text(
                    previous_value
                )
                != cls._normalise_text(
                    current_value
                )
            ):
                changed_fields.append(
                    (
                        f"{field}: "
                        f"'{previous_value or 'Not set'}' → "
                        f"'{current_value or 'Not set'}'"
                    )
                )

        method_labels = {
            "exact": "Exact match",
            "strong_identity": "Matched by audit identity",
            "fuzzy": "Matched after minor name change",
        }

        return {
            "match_method": method,
            "match_method_label": (
                method_labels.get(
                    method,
                    method.title(),
                )
            ),
            "match_score": round(
                score * 100,
                1,
            ),
            "identity_changed": bool(
                changed_fields
            ),
            "identity_change_text": "; ".join(
                changed_fields
            ),
        }

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

        text = unicodedata.normalize(
            "NFKD",
            str(value or ""),
        )

        text = "".join(
            character
            for character in text
            if not unicodedata.combining(
                character
            )
        )

        text = re.sub(
            r"[^a-zA-Z0-9]+",
            " ",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip().lower()

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