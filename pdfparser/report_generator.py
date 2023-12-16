"""Report generator."""
from typing import List, Set
from collections import defaultdict
from datetime import date, timedelta
from calendar import month_name

from pdfparser.store import Query


class ReportGenerator:
    """Generate predefined report in json format."""

    def __init__(self, query: Query) -> None:
        self._query: Query = query
        self._broker_level_data: List[
            dict
        ] = query.get_broker_level_loan_amount_with_date()

    def generate_broker_report(self) -> dict:
        """Generate all broker's report.

        Format:-

            {
                "Cheston La'Porte": {
                    "daily": {
                        "2023-10-17": [35890.0, 3589.0]
                    },
                    "weekly": {
                        "2023-10-17 - 2023-10-24": [35890.0, 3589.0]
                    },
                    "monthly": {
                        "October": [35890.0, 3589.0]
                    }
                }
            }
        """
        report: dict = defaultdict(lambda: defaultdict(dict))
        self._populate_daily_amounts(report)
        self._populate_weekly_amounts(report)
        self._populate_monthly_amounts(report)
        # Convert daily dates to string.
        for _broker_name, options in report.items():
            keys = tuple(options["daily"].keys())
            for date_ in keys:
                val: List[float] = options["daily"].pop(date_)
                options["daily"][str(date_)] = val
        return report

    def generate_total_loan_report(self) -> dict:
        """Total loan amount per day.

        Format:-

            {
                "2023-10-17": 358900.0
            }
        """
        report: dict = defaultdict(float)
        for record in self._broker_level_data:
            report[str(record["settlement_date"])] += sum(record["array_agg_1"])
        return report

    def generate_tier_level_report(self) -> dict:
        """Loan amount in each tier per day.

        Format:-

            {
                "2023-10-17": {
                    "tier1": 5,
                    "tier2": 10,
                    "tier3": 1
                }
            }
        """
        report: dict = defaultdict(dict)
        for record in self._broker_level_data:
            date_str: str = str(record["settlement_date"])
            if date_str not in report:
                report[date_str] = {"tier1": 0, "tier2": 0, "tier3": 0}
            for amount in record["array_agg_1"]:
                if amount > 1_00_000:
                    report[date_str]["tier1"] += 1
                elif amount > 50_000:
                    report[date_str]["tier2"] += 1
                elif amount > 10_000:
                    report[date_str]["tier3"] += 1

        return report

    def _populate_daily_amounts(self, report: dict) -> None:
        """Populate daily total-loan-amount in descending order."""
        for record in self._broker_level_data:
            date_node_location: dict = report[record["broker"]]["daily"]
            if record["settlement_date"] not in date_node_location:
                date_node_location[record["settlement_date"]] = record["array_agg_1"]
            else:
                date_node_location += record["array_agg_1"]
        # Sort daily total-loan-amounts.
        for _broker_name, options in report.items():
            for loan_amounts in options["daily"].values():
                loan_amounts.sort(reverse=True)

    @staticmethod
    def _populate_weekly_amounts(report: dict) -> None:
        """Populate weekly total-loan-amount in descending order."""
        for _broker_name, options in report.items():
            visited_dates: Set[date] = set()
            for date_, loan_amounts in options["daily"].items():
                if date_ in visited_dates:
                    continue
                weekly_amounts: List[float] = loan_amounts[::]
                for date_offset in range(1, 7):
                    next_date: date = date_ + timedelta(days=date_offset)
                    if next_date not in options["daily"]:
                        continue
                    visited_dates.add(next_date)
                    weekly_amounts += options["daily"][next_date]
                options["weekly"][
                    f"{str(date_)} - {str(date_ + timedelta(days=6))}"
                ] = sorted(weekly_amounts, reverse=True)
            visited_dates.clear()

    @staticmethod
    def _populate_monthly_amounts(report: dict) -> None:
        """Populate monthly total-loan-amount in descending order."""
        for _broker_name, options in report.items():
            for date_, loan_amounts in options["daily"].items():
                if month_name[date_.month] not in options["monthly"]:
                    options["monthly"][month_name[date_.month]] = loan_amounts[::]
                else:
                    options["monthly"][month_name[date_.month]] += loan_amounts
        # Sort monthly loan amounts.
        for _broker_name, options in report.items():
            for monthly_loan_amounts in options["monthly"].values():
                monthly_loan_amounts.sort(reverse=True)
