"""Table definitions."""
from sqlalchemy import (
    Table,
    Column,
    String,
    MetaData,
    BigInteger,
    Date,
    Float,
    UniqueConstraint,
)

METADATA = MetaData()


Transaction = Table(
    "Transaction",
    METADATA,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("app_id", BigInteger, nullable=False),
    Column("xref", BigInteger, nullable=False),
    Column("settlement_date", Date, nullable=False),
    Column("broker", String(250), nullable=False),
    Column("sub_broker", String(250), nullable=True),
    Column("borrower_name", String(250), nullable=False),
    Column("description", String(500), nullable=True),
    Column("total_loan_amount", Float, nullable=False),
    Column("comm_rate", Float, nullable=False),
    Column("upfront", Float, nullable=False),
    Column("upfront_incl_gst", Float, nullable=False),
    UniqueConstraint("xref", "total_loan_amount"),
)
