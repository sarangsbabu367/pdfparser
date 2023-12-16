"""Custom datastructures."""
from dataclasses import dataclass
from datetime import date


@dataclass
class TransactionRecord:
    """Record representation."""

    app_id: int
    xref: int
    settlement_date: date
    broker: str
    sub_broker: str
    borrower_name: str
    description: str
    total_loan_amount: float
    comm_rate: float
    upfront: float
    upfront_incl_gst: float
