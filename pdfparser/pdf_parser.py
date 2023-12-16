"""Convert the given pdf to usable data format.
    * Raise error, if pdf is not in intended format.
    * Raise error, if any of the transaction row is not in intended format.
    * Parse the pdf and create tuples (storable format in a database).

    Predefined pdf format:-

    App ID      Xref        Settlement Date ... Upfront Incl GST
    80185884    100305936   17/10/2023      ... 710.62

    Column names:-
    
    * App ID, Xref, Settlement Date, Broker, Sub Broker, Borrower Name, Description
      Total Loan Amount, Comm Rate, Upfront, Upfront Incl GST
"""
from typing import TextIO, List, Tuple, Optional
from datetime import date

from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
import tabula
from pandas.core.frame import DataFrame

from pdfparser.datastructure import TransactionRecord

_COLUMN_NAMES: str = (
    "AppID"
    + "Xref"
    + "SettlementDate"
    + "Broker"
    + "SubBroker"
    + "BorrowerName"
    + "Description"
    + "TotalLoanAmount"
    + "CommRate"
    + "Upfront"
    + "UpfrontInclGST"
)
_APP_ID_XREF_POS: int = 0
_SETTLEMENT_DATE_POS: int = 1
_BROKER_POS: int = 2
_SUB_BROKER_POS: int = 3
_BORROWER_NAME_DESCRIPTION_POS: int = -5
_TOTAL_LOAN_AMOUNT_POS: int = -4
_COMM_RATE_POS: int = -3
_UPFRONT_POS: int = -2
_UPFRONT_INCL_GST_POS: int = -1
_FULL_ROW_LENGTH: int = 9


class PDFParser:
    """Parse the given pdf to usable format and raise error for unformatted pdf."""

    def __init__(self, file: TextIO) -> None:
        self._file: TextIO = file

    def parse(self) -> List[TransactionRecord]:
        """Convert pdf to transaction records."""
        self._validate_pdf()

        try:
            df: DataFrame = tabula.read_pdf(
                self._file, multiple_tables=False, pages="all"
            )[0]
        except Exception as _exc:
            raise ValueError("Could not read the pdf.")

        records: List[TransactionRecord] = []
        for record_str in df.to_csv().split("\n"):
            if not record_str:
                continue
            records.append(self._form_record(record_str))

        return records

    def _validate_pdf(self) -> None:
        """Raise type-error if pdf is not valid.

        * If file name not ends with `.pdf`.
        * If unable to parse pdf with library.
        * If pdf header does not contain all required columns.
        """
        if not self._file.name.endswith(".pdf"):
            raise TypeError("Only .pdf files are supported.")

        try:
            # Trying to read pdf and extract column names from first line.
            if ("").join(
                PdfReader(self._file).pages[0].extract_text().split("GST")[0].split()
            ) + "GST" != _COLUMN_NAMES:
                raise TypeError("pdf does not contain all required columns.")
        except PdfReadError:
            raise TypeError("Invalid pdf format.")

    def _form_record(self, record_data: str) -> TransactionRecord:
        """Validate all record fields like `float`, `date` etc. then convert."""
        data: List[str] = record_data.split(",")[1:]
        # Remove `None` and `Unnamed` values.
        data = list(filter(lambda val: val and not val.startswith("Unnamed: "), data))
        self._join_float_values(data)
        app_id, xref = data[_APP_ID_XREF_POS].split(" ")
        borrower_name, description = self._form_borrower_name_and_description(
            data[_BORROWER_NAME_DESCRIPTION_POS]
        )
        sub_broker: Optional[str] = None
        if len(data) == _FULL_ROW_LENGTH:
            sub_broker = data[_SUB_BROKER_POS]
        if not borrower_name and sub_broker:
            borrower_name, sub_broker = self._form_borrower_name_and_sub_broker(
                sub_broker
            )

        return TransactionRecord(
            app_id=int(app_id),
            xref=int(xref),
            settlement_date=self._form_date(data[_SETTLEMENT_DATE_POS]),
            broker=data[_BROKER_POS],
            sub_broker=sub_broker,
            borrower_name=borrower_name,
            description=description,
            total_loan_amount=float(data[_TOTAL_LOAN_AMOUNT_POS]),
            comm_rate=float(data[_COMM_RATE_POS]),
            upfront=float(data[_UPFRONT_POS]),
            upfront_incl_gst=float(data[_UPFRONT_INCL_GST_POS]),
        )

    @staticmethod
    def _join_float_values(data: List[str]) -> None:
        """Join float values split by `,`.
        # eg: ['"35', '890.00"'] -> 35890.00
        """
        for pos, val in enumerate(data):
            if len(val) > 1 and val[0].startswith('"') and val[1].isdigit():
                iter: int = pos + 1
                while iter < len(data):
                    sub_val: str = data.pop(iter)
                    val += sub_val
                    # last piece to join for a float value.
                    if sub_val.endswith('"'):
                        break
                    iter += 1
                val = val.strip('"')
                data[pos] = val

    @staticmethod
    def _form_borrower_name_and_description(name_and_desc: str) -> Tuple[str, str]:
        """Borrowner name & description is combined after parsing pdf.

        Assumption: Borrower name will be capitalised always in given data.

        eg: CHELSEA BIANCA VANDERAA Upfront Commission
        """
        name_and_desc_split: List[str] = name_and_desc.split(" ")
        for pos, sub_str in enumerate(name_and_desc_split):
            # found the separation position.
            if sub_str != sub_str.upper():
                return (
                    " ".join(name_and_desc_split[:pos]),
                    " ".join(name_and_desc_split[pos:]),
                )
        raise ValueError(
            f"Unable to find borrower-name & description from '{name_and_desc}'"
        )

    @staticmethod
    def _form_borrower_name_and_sub_broker(sub_broker_and_name: str) -> Tuple[str, str]:
        """Form borrower name & sub broker if borrower name is not along with
        description.

        Assumption: Borrower name will be capitalised always in given data.

        eg: Aagam Pabari ANJAN GUPTA
            Rhiannon Clancy-BurnsSARA FLOWER

        """
        for pos in range(len(sub_broker_and_name) - 1, -1, -1):
            if not sub_broker_and_name[pos].isalpha():
                continue
            # Found the separation index.
            if sub_broker_and_name[pos] != sub_broker_and_name[pos].upper():
                return (
                    sub_broker_and_name[pos + 1 :].strip(),
                    sub_broker_and_name[: pos + 1].strip(),
                )
        return sub_broker_and_name, ""

    @staticmethod
    def _form_date(date_str: str) -> date:
        """Form date object from date string in format `dd/mm/yyyy`"""
        day, month, year = date_str.split("/")
        return date(day=int(day), month=int(month), year=int(year))
