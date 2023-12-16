"""A module to execute functionalities."""
from typing import List, Optional
from datetime import date
from pprint import pprint

from sqlalchemy import Engine
from sqlalchemy.exc import ProgrammingError

from pdfparser.pdf_parser import PDFParser
from pdfparser.datastructure import TransactionRecord
from pdfparser.store import Init, Mutation, Query
from pdfparser.report_generator import ReportGenerator


if __name__ == "__main__":
    try:
        # todo: remove
        # eg: db_constructor: Init = Init("nick", "", "localhost", 5432, "transaction_db")
        db_constructor: Init = Init("<username>", "<password>", "<host>", "<port>", "<db_name>")
        try:
            db_constructor.create_db()
        # Skipping DB already exists error (DB should be created only once.)
        except ProgrammingError:
            pass
        engine: Engine = db_constructor.create_engine()
        # ---------------------------------------------------------------------------
        # todo: remove
        # eg: with open("/Users/nick/pdfparser/tests/transaction.pdf", "rb") as source:
        with open("</path-to/transaction.pdf>", "rb") as source:
            records: List[TransactionRecord] = PDFParser(source).parse()
        # ---------------------------------------------------------------------------
        mutation: Mutation = Mutation(engine)
        mutation.insert_transactions(records)
        # ---------------------------------------------------------------------------
        query: Query = Query(engine)
        total_loan_amount: Optional[float] = query.get_loan_amount(
            date(day=17, month=10, year=2023), date(day=25, month=10, year=2023)
        )
        print("Total loan amount from 2023-10-17 to 2023-10-25", "\n")
        print(total_loan_amount, "\n\n")
        max_loan_amount_by_broker: Optional[
            float
        ] = query.get_highest_loan_amt_by_broker("Cheston La'Porte")
        print("Maximum loan amount by 'Cheston La'Porte'", "\n")
        print(max_loan_amount_by_broker, "\n\n")
        # ---------------------------------------------------------------------------
        report_generator: ReportGenerator = ReportGenerator(query)
        broker_report: dict = report_generator.generate_broker_report()
        total_loan_amount_report: dict = report_generator.generate_total_loan_report()
        tier_level_report: dict = report_generator.generate_tier_level_report()
        print("Broker level report", "\n")
        pprint(broker_report)
        print("\n\n")
        print("Total loan amount report", "\n")
        pprint(total_loan_amount_report)
        print("\n\n")
        print("Tier level report", "\n")
        pprint(tier_level_report)
    finally:
        # Dispose engine after use.
        engine.dispose()
