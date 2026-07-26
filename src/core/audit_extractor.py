import re
from collections.abc import Callable
from typing import Any
from playwright.sync_api import Page, sync_playwright

from src.services.aseat_url_service import ASeatUrlService


ProgressCallback = Callable[[int, str], None]


class AuditExtractor:
    """Extracts audit progress information from A-SEAT."""

    AUDIT_LIST_PATH = "/system/business_audit/project_list.php"

    def __init__(
        self,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self._progress_callback = progress_callback

    def _report_progress(
        self,
        percentage: int,
        message: str,
    ) -> None:
        if self._progress_callback is not None:
            self._progress_callback(percentage, message)

    @staticmethod
    def build_audit_list_url(configured_url: str) -> str:
        """Build the A-SEAT audit-list address from the saved URL."""

        return ASeatUrlService.resolve(
            configured_url
        ).audit_list_url

    @staticmethod
    def _login(
        page: Page,
        username: str,
        password: str,
    ) -> None:
        """Log in when the A-SEAT login form is displayed."""

        # The requested page may already be authenticated.
        if page.locator("#logout_btn").count() > 0:
            return

        username_selector = (
            "#user_login, input[name='user'], "
            "input[name='user_login']"
        )
        password_selector = (
            "#user_pass, input[name='pwd'], "
            "input[name='user_pass'], input[type='password']"
        )
        submit_selector = (
            "#submit, form#loginform input[type='submit'], "
            "input[type='submit'][value='Login'], "
            "button[type='submit']"
        )

        try:
            page.locator(username_selector).first.wait_for(
                state="visible",
                timeout=30_000,
            )
            page.locator(password_selector).first.wait_for(
                state="visible",
                timeout=30_000,
            )

        except Exception as error:
            raise RuntimeError(
                "The A-SEAT login form could not be detected.\n\n"
                f"Current page: {page.url}\n"
                f"Page title: {page.title()}"
            ) from error

        page.locator(username_selector).first.fill(username)
        page.locator(password_selector).first.fill(password)

        submit_button = page.locator(submit_selector).first

        if submit_button.count() == 0:
            raise RuntimeError(
                "The A-SEAT login button could not be detected."
            )

        submit_button.click()

        try:
            page.wait_for_load_state(
                "domcontentloaded",
                timeout=60_000,
            )
        except Exception:
            pass

        page.wait_for_timeout(1_000)

        if page.locator(username_selector).count() > 0:
            login_error = ""

            if page.locator("#login_status").count() > 0:
                login_error = (
                    page.locator("#login_status")
                    .inner_text()
                    .strip()
                )

            if login_error:
                raise RuntimeError(
                    f"A-SEAT login failed: {login_error}"
                )

            raise RuntimeError(
                "A-SEAT login was not successful. "
                "Check the username and password."
            )

    @staticmethod
    def _normalise_heading(value: str) -> str:
        return re.sub(
            r"[^a-z0-9]+",
            " ",
            value.lower(),
        ).strip()

    @staticmethod
    def _find_heading_index(
        headings: list[str],
        *possible_names: str,
    ) -> int | None:
        for index, heading in enumerate(headings):
            for possible_name in possible_names:
                if possible_name in heading:
                    return index

        return None

    def _extract_table_rows(
        self,
        page: Page,
    ) -> list[dict[str, str]]:
        """Extract the required fields from the visible audit-list table."""

        page.wait_for_selector(
            "text=/Audit List For Year/i",
            timeout=60_000,
        )

        header = page.locator(
            "text=/Audit List For Year/i"
        ).first

        table = header.locator(
            "xpath=ancestor::table[1]"
        )

        if table.count() == 0:
            raise RuntimeError(
                "The audit-list table could not be detected."
            )

        header_names: list[str] = table.evaluate(
            """
            table => {
                const rows = Array.from(
                    table.querySelectorAll("tr")
                );

                let bestHeadings = [];

                for (const row of rows) {
                    const cells = Array.from(
                        row.querySelectorAll(
                            ":scope > th, :scope > td"
                        )
                    );

                    const values = cells.map(cell =>
                        (
                            cell.innerText ||
                            cell.textContent ||
                            ""
                        )
                        .replace(/\\s+/g, " ")
                        .trim()
                    );

                    const looksLikeHeader = values.some(value =>
                        /auditee|audit name|progress|audit year/i.test(
                            value
                        )
                    );

                    if (
                        looksLikeHeader &&
                        values.length > bestHeadings.length
                    ) {
                        bestHeadings = values;
                    }
                }

                return bestHeadings;
            }
            """
        )

        normalised_headers = [
            self._normalise_heading(str(value))
            for value in header_names
        ]

        header_indexes = {
            "auditee": self._find_heading_index(
                normalised_headers,
                "auditee",
            ),
            "directorate": self._find_heading_index(
                normalised_headers,
                "directorate",
            ),
            "audit_name": self._find_heading_index(
                normalised_headers,
                "audit name",
            ),
            "audit_lead": self._find_heading_index(
                normalised_headers,
                "audit lead",
                "team leader",
            ),
            "audit_type": self._find_heading_index(
                normalised_headers,
                "audit type",
            ),
            "start_date": self._find_heading_index(
                normalised_headers,
                "planned start",
                "start date",
            ),
            "completion_date": self._find_heading_index(
                normalised_headers,
                "planned completion",
                "completion date",
            ),
            "audit_year": self._find_heading_index(
                normalised_headers,
                "audit year",
            ),
            "progress": self._find_heading_index(
                normalised_headers,
                "progress",
            ),
        }

        extracted_rows: list[dict[str, str]] = []
        rows = table.locator("tr")

        for row_index in range(rows.count()):
            row = rows.nth(row_index)

            # Data rows contain a View button.
            if row.locator("input[value='View']").count() == 0:
                continue

            cell_values: list[str] = row.evaluate(
                """
                row => {
                    let cells = Array.from(row.children)
                        .filter(element => element.tagName === "TD");

                    if (cells.length < 8) {
                        cells = Array.from(
                            row.querySelectorAll("td")
                        );
                    }

                    function extractCellValue(cell) {
                        const text = (
                            cell.innerText ||
                            cell.textContent ||
                            ""
                        )
                        .replace(/\\s+/g, " ")
                        .trim();

                        if (text) {
                            return text;
                        }

                        const input = cell.querySelector(
                            "input:not([type='button'])" +
                            ":not([type='submit']), textarea"
                        );

                        if (input && input.value) {
                            return String(input.value).trim();
                        }

                        const select = cell.querySelector("select");

                        if (select) {
                            const option =
                                select.options[
                                    select.selectedIndex
                                ];

                            if (option) {
                                return (
                                    option.text ||
                                    option.value ||
                                    ""
                                ).trim();
                            }
                        }

                        const progressElement =
                            cell.querySelector(
                                "progress, " +
                                "[role='progressbar'], " +
                                "[aria-valuenow], " +
                                "[data-progress], " +
                                "[data-percent], " +
                                "[title*='%']"
                            );

                        if (progressElement) {
                            const value =
                                progressElement.getAttribute(
                                    "aria-valuenow"
                                ) ||
                                progressElement.getAttribute(
                                    "data-progress"
                                ) ||
                                progressElement.getAttribute(
                                    "data-percent"
                                ) ||
                                progressElement.getAttribute(
                                    "value"
                                ) ||
                                progressElement.getAttribute(
                                    "title"
                                );

                            if (value) {
                                const cleaned =
                                    String(value).trim();

                                return cleaned.includes("%")
                                    ? cleaned
                                    : cleaned + "%";
                            }
                        }

                        return (
                            cell.getAttribute("value") ||
                            cell.getAttribute("title") ||
                            cell.getAttribute("data-value") ||
                            ""
                        ).trim();
                    }

                    return cells.map(extractCellValue);
                }
                """
            )

            if len(cell_values) < 8:
                continue

            def get_value(
                detected_index: int | None,
                fallback_index: int,
            ) -> str:
                selected_index = (
                    detected_index
                    if detected_index is not None
                    else fallback_index
                )

                if not 0 <= selected_index < len(cell_values):
                    return ""

                return str(
                    cell_values[selected_index]
                ).strip()

            auditee_name = get_value(
                header_indexes["auditee"],
                1,
            )

            if (
                not auditee_name
                or auditee_name.lower() == "auditee name"
            ):
                continue

            audit_year = get_value(
                header_indexes["audit_year"],
                8,
            )

            progress = get_value(
                header_indexes["progress"],
                10,
            )

            audit_years = re.findall(
                r"\b20\d{2}\b",
                audit_year,
            )

            if audit_years:
                audit_year = ", ".join(
                    dict.fromkeys(audit_years)
                )

            year_progress_pairs = re.findall(
                r"\b(20\d{2})\s*:\s*"
                r"(\d+(?:\.\d+)?)\s*%",
                progress,
            )

            if year_progress_pairs:
                progress = "\n".join(
                    f"{year}: {percentage}%"
                    for year, percentage in year_progress_pairs
                )
            else:
                percentages = re.findall(
                    r"\d+(?:\.\d+)?\s*%",
                    progress,
                )

                if percentages:
                    progress = "\n".join(
                        value.replace(" ", "")
                        for value in percentages
                    )

            extracted_rows.append(
                {
                    "Auditee Name": auditee_name,
                    "Directorate": get_value(
                        header_indexes["directorate"],
                        2,
                    ),
                    "Audit Name": get_value(
                        header_indexes["audit_name"],
                        3,
                    ),
                    "Audit Lead": get_value(
                        header_indexes["audit_lead"],
                        4,
                    ),
                    "Audit Type": get_value(
                        header_indexes["audit_type"],
                        5,
                    ),
                    "Planned Start Date": get_value(
                        header_indexes["start_date"],
                        6,
                    ),
                    "Planned Completion Date": get_value(
                        header_indexes["completion_date"],
                        7,
                    ),
                    "Audit Year": audit_year,
                    "Progress": progress,
                }
            )

        if not extracted_rows:
            raise RuntimeError(
                "No audit records were extracted from the page."
            )

        return extracted_rows

    def extract(
        self,
        configured_url: str,
        username: str,
        password: str,
        show_browser: bool = True,
    ) -> list[dict[str, Any]]:
        """Open A-SEAT, authenticate and extract the audit list."""

        if not username.strip():
            raise ValueError("A username is required.")

        if not password:
            raise ValueError("A password is required.")

        audit_list_url = self.build_audit_list_url(
            configured_url
        )

        self._report_progress(
            5,
            "Starting browser",
        )

        with sync_playwright() as playwright:
            browser = None

            try:
                browser = playwright.chromium.launch(
                    channel="msedge",
                    headless=not show_browser,
                )

                page = browser.new_page(
                    viewport={
                        "width": 1600,
                        "height": 1000,
                    }
                )

                self._report_progress(
                    15,
                    "Opening A-SEAT",
                )

                page.goto(
                    audit_list_url,
                    wait_until="domcontentloaded",
                    timeout=60_000,
                )

                self._report_progress(
                    30,
                    "Authenticating",
                )

                self._login(
                    page,
                    username.strip(),
                    password,
                )

                self._report_progress(
                    45,
                    "Opening audit list",
                )

                page.goto(
                    audit_list_url,
                    wait_until="domcontentloaded",
                    timeout=60_000,
                )

                self._report_progress(
                    65,
                    "Extracting audit records",
                )

                extracted_rows = (
                    self._extract_table_rows(page)
                )

                self._report_progress(
                    80,
                    (
                        f"Extracted "
                        f"{len(extracted_rows)} audit records"
                    ),
                )

                return extracted_rows

            finally:
                if browser is not None:
                    try:
                        browser.close()
                    except Exception:
                        pass