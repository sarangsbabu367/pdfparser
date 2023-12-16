"""All store handlers (All apis to handle database.)"""
from typing import Optional, List
from datetime import date

from sqlalchemy.engine.base import Engine
from sqlalchemy import create_engine, text, Table, insert, select, func, and_
from sqlalchemy.exc import IntegrityError

from pdfparser.models import METADATA
from pdfparser.datastructure import TransactionRecord

_DEFAULT_POSTFRES_DB_NAME: str = "postgres"


class Init:
    """Database constructor.

    * Create database.
    * Create tables.

    NOTE: DB details are read from `.env` file.
    """

    def __init__(
        self, username: str, password: str, host: str, port: int, db_name: str
    ) -> None:
        self._username: str = username
        self._password: str = password
        self._host: str = host
        self._port: int = port
        self._db_name: str = db_name

    def create_db(self) -> None:
        """Create database and tables using metadata."""
        default_engine: Engine = self.create_engine(_DEFAULT_POSTFRES_DB_NAME)

        with default_engine.connect() as conn:
            conn.execute(text(f"create database {self._db_name}"))
            curr_engine: Engine = self.create_engine()
            METADATA.create_all(curr_engine)
            curr_engine.dispose()
        default_engine.dispose()

    def drop_db(self) -> None:
        """Delete the entire database.

        WARNING: ALL EXISTING DB-DATA WILL BE LOST IF CALLED.
        """
        default_engine: Engine = self.create_engine(_DEFAULT_POSTFRES_DB_NAME)

        with default_engine.connect() as conn:
            conn.execute(text(f"drop database {self._db_name}"))
        default_engine.dispose()

    def create_engine(self, db_name: Optional[str] = None) -> Engine:
        """Create a database engine for creating database connection.

        Engine should be disposed after use, otherwise connection leak will happen.
        """
        db_name_: str = db_name if db_name else self._db_name
        return create_engine(
            f"postgresql://{self._username}:{self._password}@{self._host}:{self._port}/{db_name_}"
        ).execution_options(isolation_level="AUTOCOMMIT")


class Mutation:
    """Data manipulation apis."""

    def __init__(self, engine: Engine) -> None:
        self._engine: Engine = engine

    def insert_transactions(self, transactions: List[TransactionRecord]) -> None:
        """Insert all records to database.

        In case of `UniqueConstraint` error, skip the error.
        For avoiding duplicate records in DB, unique-constraint is used.
        """
        transaction_table: Table = METADATA.tables["Transaction"]
        with self._engine.connect() as conn:
            for record in transactions:
                stmt = insert(transaction_table).values(
                    app_id=record.app_id,
                    xref=record.xref,
                    settlement_date=record.settlement_date,
                    broker=record.broker,
                    sub_broker=record.sub_broker,
                    borrower_name=record.borrower_name,
                    description=record.description,
                    total_loan_amount=record.total_loan_amount,
                    comm_rate=record.comm_rate,
                    upfront=record.upfront,
                    upfront_incl_gst=record.upfront_incl_gst,
                )
                try:
                    conn.execute(stmt)

                except IntegrityError as exc:
                    # Skipping `UniqueConstraint` error for maintaining unique records
                    # with (xref + total-loan-amount)
                    if exc.orig.pgcode == "23505":
                        continue
                    raise exc


class Query:
    """Data querying apis."""

    def __init__(self, engine: Engine) -> None:
        self._engine: Engine = engine

    def get_loan_amount(self, start_date: date, end_date: date) -> Optional[float]:
        """Loan amount in a period."""
        transaction_table: Table = METADATA.tables["Transaction"]
        stmt = select(func.sum(transaction_table.columns["total_loan_amount"])).where(
            and_(
                transaction_table.columns["settlement_date"] >= start_date,
                transaction_table.columns["settlement_date"] <= end_date,
            )
        )

        with self._engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
        return None if not result else result[0]

    def get_highest_loan_amt_by_broker(self, broker: str) -> Optional[float]:
        """Highest loan amount given by a broker."""
        transaction_table: Table = METADATA.tables["Transaction"]
        stmt = select(func.max(transaction_table.columns["total_loan_amount"])).where(
            transaction_table.columns["broker"] == broker
        )

        with self._engine.connect() as conn:
            result = conn.execute(stmt).fetchone()
        return None if not result else result[0]
