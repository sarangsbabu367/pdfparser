# pdfparser

A pdf parser which parse a predefined tabular data in pdf.


## Problem description

You are given a tax invoice statement in the form of a PDF file that contains transaction details.
Your task is to design a system that can extract transactions from the PDF, eliminate any
duplicate entries, and perform operations on the cleaned dataset.
Note: Candidates are encouraged to use appropriate programming languages and tools for
PDF parsing, data manipulation, and SQL operations in their solutions.

### Part 1: Data Extraction

Develop a script or program to take a pdf as input and extract transaction details from the
provided tax invoice PDF file. The information includes App ID, Xref, Settlement Date, Broker,
Sub Broker, Borrower Name, Description, Total Loan Amount, Commission Rate, Upfront,
Upfront Incl GST.

### Part 2: Data Storage

Store the extracted data in a database(file can also be used as datastore), so that the
information is available when required.

### Part 3: Deduplication

Implement a deduplication mechanism to identify and remove any duplicate transactions from
the extracted dataset. Transactions should be considered duplicates if they have the same Xref
and Total Loan Amount. If the same file is uploaded multiple times, the datastore should not
store multiple instances of the same transaction.

### Part 4: SQL Operations

Design a set of SQL operations to analyse the dataset. Perform the following tasks:
1. Calculate the total loan amount during a specific time period.
2. Calculate the highest loan amount given by a broker.

### Part 5: Reporting

1. Generate a report for the broker, sorting loan amounts in descending order from
maximum to minimum, covering daily, weekly, and monthly periods.
2. Generate a report of the total loan amount grouped by date.
3. Define tier level of each transaction, based on the following criteria
a. Tier 1 : Total Loan Amount > 1,00,000
b. Tier 2 : Total Loan Amount > 50,000
c. Tier 3 : Total Loan Amount > 10,000
4. Generate a report of the number of loans under each tier group by date.

ps: The sample `.pdf` file which contains transactions is present in `tests` folder named `transaction.pdf`.

## Solution

### Part 1: Data Extraction

Data extraction from `.pdf` file is done in [pdf_parser.py](pdfparser/pdf_parser.py) module.

The class named `PDFParser` take `.pdf` file as input and `parse` method can be used to parse the pdf file to predefined [TransactionRecord](pdfparser/datastructure.py) structure (line 7).

`PDFParser` class uses [PyPDF2](https://github.com/talumbau/PyPDF2) and [tabula-py](https://github.com/chezou/tabula-py) libraries to validate and parse data from `.pdf` file.

If the given pdf file is in predefined format and all records contain proper values, calling `parse` method will convert the file to list of `TransactionRecord` objects (An intermediate representation of a record).

Different types of errors are handled in this phase, currently python's inbuilt exceptions are used for raising errors. Need to add a wrapper and map exceptions to predefined errors if more convenient errors are needed for end user.

The different types of errors which is handled are,

* Given file is not pdf.
* pdf file does not contain all required predefined columns.
* pdf is not in predefined format.
* Unable to parse the pdf.
* Unformatted date.
* Unformatted int & float values.

### Part 2: Data Storage

All database related apis are defined in [store.py](pdfparser/store.py).

The module consists of 3 classes,

#### class Init

A constructor for initialising the databae (create database & table).

#### class Mutaion

All data manipulation (create/update/delete) related apis are defined in this class.

#### class Query

All data querying apis are defined in this class.

For saving the transaction details, the result from `PDFParser.parse` can be passed to `Mutation.insert_transactions` method. This method will return all transactions in the database.

Classes Query, Mutation requires an attribute `engine` (To make database connection) which can be retrieved using `Init.create_engine`.

### Part 3: Deduplication

Deduplication of records with same `xref` and `Total loan amount` is handled in db layer.

The `Transaction` table which stores all transaction records is defined in [models.py](pdfparser/models.py). A `UniqueConstraint` is added for combination of `xref` & `total_loan_amount` columns. This will ensure there are no duplicate records in database. Whenever we try to save a duplicate record (like trying to save the same result again and again) a database `IntegrityError` will be raised. If this error is occurred while trying to save a record using `Mutation.insert_transactions`, the record is skipped (avoiding duplicate records). So that end user wont see the error due to duplicate record and program wont crash.

### Part 4: SQL Operations

To get the data based on criterias `Query` class from [store.py](pdfparser/store.py) can be used.

1. Calculate the total loan amount during a specific time period.

`Query.get_loan_amount` method can be used to get the above info by providing `start_date` & `end_date` of the period.

ps: Method will return `None` if there is no data in the given time period.

2. Calculate the highest loan amount given by a broker.

`Query.get_highest_loan_amt_by_broker` method can be used to get the above info providing `broker` name.

ps: Method will return `None` if there is no data for the given broker.

### Part 5: Reporting

All report handling is done done by `ReportGenerator` class in [report_generator.py](pdfparser/report_generator.py). `ReportGenerator` requires a query attribute which is an object of `Query` class (described above) for fetching data from database.

Reports will be returned in python's `dict` format which can be converted to `json` if needed.

There are 3 apis to fetch the 3 types of reports.

#### Broker level report

Method:-

    generate_broker_report

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

#### Total loan amount report

Method:-

    generate_total_loan_report

Format:-

    {
        "2023-10-17": 358900.0
    }

#### Tier level report

Method:-

    generate_tier_level_report

Format:-

    {
        "2023-10-17": {
            "tier1": 5,
            "tier2": 10,
            "tier3": 1
        }
    }

## How to use

### Prerequisites

1. Install [postgresql](https://www.postgresql.org/download/) if not installed in the machine. `postgres` is used as database.

    ps: You can check whether `postgres` is installed or not by running `psql` command from terminal.

    ```zsh
    ➜  ~ psql
    psql (14.9 (Homebrew))
    Type "help" for help.

    nick=# 
    ```

2. Create and activate an environment for installing dependencies.

    ```zsh
    ➜  pdfparser git:(feat_pdf_to_data_converter) ✗ 
    ➜  pdfparser git:(feat_pdf_to_data_converter) ✗ python3 -m venv env_transaction
    ➜  pdfparser git:(feat_pdf_to_data_converter) ✗ source env_transaction/bin/activate
    (env_transaction) ➜  pdfparser git:(feat_pdf_to_data_converter) ✗ 
    ```
3. Install [poetry](https://python-poetry.org/docs/basic-usage/) and dependencies.

    ```zsh
    (env_transaction) ➜  pdfparser git:(feat_pdf_to_data_converter) ✗ pip install poetry
    (env_transaction) ➜  pdfparser git:(feat_pdf_to_data_converter) ✗ poetry install
    ```

A module named [main.py](pdfparser/main.py) is included in the package for running all the functionalities.

2 things needs to be changed to execute the file,

1. Change the db related parameters ("<username>", "<password>", "<host>", "<port>", "<db_name>") before initialising `Init` object.
2. Change `</path-to/transaction.pdf>` with exact path of pdf with predefined format (sample is present in tests folder named `transaction.pdf`)

After changing the above mentioned placeholders, run the file from terminal.

```zsh
(env_transaction) ➜  pdfparser git:(feat_pdf_to_data_converter) ✗ python pdfparser/main.py
```

ps: If any of the result is not needed in terminal comment or remove it before executing the file.

### Explanation of each section in [main.py](pdfparser/main.py)

1. The first section is for setting up the db.
    * `db_constructor.create_db()` will create database & tables (Error related to creating existing database is caught and skipped for running the file multiple times. Otherwise database needs to be dropped).
    * `engine` is required for other upcoming objects, to make database connection.
2. This part opens the `.pdf` containing transactions and convert it to a convenient intermediate format for processing.
3. This part saves the transaction records got from step2 in database by calling `mutation.insert_transactions(records)`
4. This part get the details from database using store apis.
    * `query.get_loan_amount` returns the total loan amount in a period.
    * `query.get_highest_loan_amt_by_broker` returns the highest loan amount by broker.
5. This section generates the 3 predefined types of report in json format using `ReportGenerator` object. Formats of all report types are described in [solution/reporting](#part-5-reporting-1) section.
    * `report_generator.generate_broker_report` returns broker specific loan amount.
    * `report_generator.generate_total_loan_report` returns total loan amount per day.
    * `report_generator.generate_tier_level_report` returns tier level count of loan amount.

## Sample result

```zsh
(env_transaction) ➜  pdfparser git:(feat_pdf_to_data_converter) ✗ python pdfparser/main.py
Error importing jpype dependencies. Fallback to subprocess.
No module named 'jpype'
Total loan amount from 2023-10-17 to 2023-10-25 

1176340.4000000001 


Maximum loan amount by 'Cheston La'Porte' 

59060.2 


Broker level report 

defaultdict(<function ReportGenerator.generate_broker_report.<locals>.<lambda> at 0x128d66790>,
            {'Alexander Foldi': defaultdict(<class 'dict'>,
                                            {'daily': {'2023-10-05': [37490.0],
                                                       '2023-10-23': [70744.0]},
                                             'monthly': {'October': [70744.0,
                                                                     37490.0]},
                                             'weekly': {'2023-10-05 - 2023-10-11': [37490.0],
                                                        '2023-10-23 - 2023-10-29': [70744.0]}}),
             'Anthony Mansour': defaultdict(<class 'dict'>,
                                            {'daily': {'2023-10-25': [48884.0]},
                                             'monthly': {'October': [48884.0]},
                                             'weekly': {'2023-10-25 - 2023-10-31': [48884.0]}}),
             'Antony Forato': defaultdict(<class 'dict'>,
                                          {'daily': {'2023-10-12': [53776.5]},
                                           'monthly': {'October': [53776.5]},
                                           'weekly': {'2023-10-12 - 2023-10-18': [53776.5]}}),
             'Approve Finance Pty Ltd': defaultdict(<class 'dict'>,
                                                    {'daily': {'2023-10-30': [59933.81]},
                                                     'monthly': {'October': [59933.81]},
                                                     'weekly': {'2023-10-30 - 2023-11-05': [59933.81]}}),
             'Auswide Financial Solutions Pty Ltd': defaultdict(<class 'dict'>,
                                                                {'daily': {'2023-10-03': [27625.0],
                                                                           '2023-10-16': [38770.0],
                                                                           '2023-10-17': [17168.11],
                                                                           '2023-10-18': [54342.99],
                                                                           '2023-10-25': [67085.07],
                                                                           '2023-10-27': [35000.0]},
                                                                 'monthly': {'October': [67085.07,
                                                                                         54342.99,
                                                                                         38770.0,
                                                                                         35000.0,
                                                                                         27625.0,
                                                                                         17168.11]},
                                                                 'weekly': {'2023-10-03 - 2023-10-09': [27625.0],
                                                                            '2023-10-16 - 2023-10-22': [54342.99,
                                                                                                        38770.0,
                                                                                                        17168.11],
                                                                            '2023-10-25 - 2023-10-31': [67085.07,
                                                                                                        35000.0]}}),
             "Cheston La'Porte": defaultdict(<class 'dict'>,
                                             {'daily': {'2023-10-06': [59060.2],
                                                        '2023-10-17': [35890.0],
                                                        '2023-10-26': [29600.0,
                                                                       28390.0]},
                                              'monthly': {'October': [59060.2,
                                                                      35890.0,
                                                                      29600.0,
                                                                      28390.0]},
                                              'weekly': {'2023-10-06 - 2023-10-12': [59060.2],
                                                         '2023-10-17 - 2023-10-23': [35890.0],
                                                         '2023-10-26 - 2023-11-01': [29600.0,
                                                                                     28390.0]}}),
             'Chris Doyle': defaultdict(<class 'dict'>,
                                        {'daily': {'2023-10-02': [60604.6],
                                                   '2023-10-11': [49390.0]},
                                         'monthly': {'October': [60604.6,
                                                                 49390.0]},
                                         'weekly': {'2023-10-02 - 2023-10-08': [60604.6],
                                                    '2023-10-11 - 2023-10-17': [49390.0]}}),
             'Chris Stafford': defaultdict(<class 'dict'>,
                                           {'daily': {'2023-10-02': [27160.0],
                                                      '2023-10-12': [19170.0],
                                                      '2023-10-24': [83794.51]},
                                            'monthly': {'October': [83794.51,
                                                                    27160.0,
                                                                    19170.0]},
                                            'weekly': {'2023-10-02 - 2023-10-08': [27160.0],
                                                       '2023-10-12 - 2023-10-18': [19170.0],
                                                       '2023-10-24 - 2023-10-30': [83794.51]}}),
             'Daniel Dahu': defaultdict(<class 'dict'>,
                                        {'daily': {'2023-10-04': [57610.0]},
                                         'monthly': {'October': [57610.0]},
                                         'weekly': {'2023-10-04 - 2023-10-10': [57610.0]}}),
             'Daniel Namonyo': defaultdict(<class 'dict'>,
                                           {'daily': {'2023-10-09': [60418.0]},
                                            'monthly': {'October': [60418.0]},
                                            'weekly': {'2023-10-09 - 2023-10-15': [60418.0]}}),
             'Demi McAndrew': defaultdict(<class 'dict'>,
                                          {'daily': {'2023-10-17': [48880.0]},
                                           'monthly': {'October': [48880.0]},
                                           'weekly': {'2023-10-17 - 2023-10-23': [48880.0]}}),
             'Evette Abdo': defaultdict(<class 'dict'>,
                                        {'daily': {'2023-10-10': [73400.07]},
                                         'monthly': {'October': [73400.07]},
                                         'weekly': {'2023-10-10 - 2023-10-16': [73400.07]}}),
             'F1 Finance': defaultdict(<class 'dict'>,
                                       {'daily': {'2023-10-05': [49210.0]},
                                        'monthly': {'October': [49210.0]},
                                        'weekly': {'2023-10-05 - 2023-10-11': [49210.0]}}),
             'F1 Finance Pty Ltd': defaultdict(<class 'dict'>,
                                               {'daily': {'2023-10-04': [41610.0],
                                                          '2023-10-10': [53600.0]},
                                                'monthly': {'October': [53600.0,
                                                                        41610.0]},
                                                'weekly': {'2023-10-04 - 2023-10-10': [53600.0,
                                                                                       41610.0]}}),
             'Hayden Clancy-Anson': defaultdict(<class 'dict'>,
                                                {'daily': {'2023-10-02': [68586.46]},
                                                 'monthly': {'October': [68586.46]},
                                                 'weekly': {'2023-10-02 - 2023-10-08': [68586.46]}}),
             'Hayley Ognenis': defaultdict(<class 'dict'>,
                                           {'daily': {'2023-10-09': [40840.98]},
                                            'monthly': {'October': [40840.98]},
                                            'weekly': {'2023-10-09 - 2023-10-15': [40840.98]}}),
             'Jacob Weir': defaultdict(<class 'dict'>,
                                       {'daily': {'2023-10-10': [51610.0]},
                                        'monthly': {'October': [51610.0]},
                                        'weekly': {'2023-10-10 - 2023-10-16': [51610.0]}}),
             'Jason Donney': defaultdict(<class 'dict'>,
                                         {'daily': {'2023-10-02': [37745.0]},
                                          'monthly': {'October': [37745.0]},
                                          'weekly': {'2023-10-02 - 2023-10-08': [37745.0]}}),
             'Joel Pettas': defaultdict(<class 'dict'>,
                                        {'daily': {'2023-10-02': [41600.0],
                                                   '2023-10-10': [57389.98]},
                                         'monthly': {'October': [57389.98,
                                                                 41600.0]},
                                         'weekly': {'2023-10-02 - 2023-10-08': [41600.0],
                                                    '2023-10-10 - 2023-10-16': [57389.98]}}),
             'Julien Cordima': defaultdict(<class 'dict'>,
                                           {'daily': {'2023-10-06': [35380.0]},
                                            'monthly': {'October': [35380.0]},
                                            'weekly': {'2023-10-06 - 2023-10-12': [35380.0]}}),
             'Justin Hilliard': defaultdict(<class 'dict'>,
                                            {'daily': {'2023-10-26': [46780.0]},
                                             'monthly': {'October': [46780.0]},
                                             'weekly': {'2023-10-26 - 2023-11-01': [46780.0]}}),
             'KCC Brokerage Pty Ltd': defaultdict(<class 'dict'>,
                                                  {'daily': {'2023-10-06': [35710.0]},
                                                   'monthly': {'October': [35710.0]},
                                                   'weekly': {'2023-10-06 - 2023-10-12': [35710.0]}}),
             'Kevin Smith': defaultdict(<class 'dict'>,
                                        {'daily': {'2023-10-09': [81620.0,
                                                                  25840.0],
                                                   '2023-10-23': [17628.34]},
                                         'monthly': {'October': [81620.0,
                                                                 25840.0,
                                                                 17628.34]},
                                         'weekly': {'2023-10-09 - 2023-10-15': [81620.0,
                                                                                25840.0],
                                                    '2023-10-23 - 2023-10-29': [17628.34]}}),
             'Lendcorp Finance': defaultdict(<class 'dict'>,
                                             {'daily': {'2023-10-27': [44585.0]},
                                              'monthly': {'October': [44585.0]},
                                              'weekly': {'2023-10-27 - 2023-11-02': [44585.0]}}),
             'Louis Fok': defaultdict(<class 'dict'>,
                                      {'daily': {'2023-10-25': [36490.0]},
                                       'monthly': {'October': [36490.0]},
                                       'weekly': {'2023-10-25 - 2023-10-31': [36490.0]}}),
             'Marco Cooper': defaultdict(<class 'dict'>,
                                         {'daily': {'2023-10-05': [33490.0,
                                                                   26390.0],
                                                    '2023-10-09': [41594.0]},
                                          'monthly': {'October': [41594.0,
                                                                  33490.0,
                                                                  26390.0]},
                                          'weekly': {'2023-10-05 - 2023-10-11': [41594.0,
                                                                                 33490.0,
                                                                                 26390.0]}}),
             'Martin Rees': defaultdict(<class 'dict'>,
                                        {'daily': {'2023-10-09': [24171.58]},
                                         'monthly': {'October': [24171.58]},
                                         'weekly': {'2023-10-09 - 2023-10-15': [24171.58]}}),
             'Matocanza Family Trust': defaultdict(<class 'dict'>,
                                                   {'daily': {'2023-10-24': [17845.41]},
                                                    'monthly': {'October': [17845.41]},
                                                    'weekly': {'2023-10-24 - 2023-10-30': [17845.41]}}),
             'Matthew Nicol': defaultdict(<class 'dict'>,
                                          {'daily': {'2023-10-27': [65581.1]},
                                           'monthly': {'October': [65581.1]},
                                           'weekly': {'2023-10-27 - 2023-11-02': [65581.1]}}),
             'Michael Papageorgiou': defaultdict(<class 'dict'>,
                                                 {'daily': {'2023-10-17': [54588.07]},
                                                  'monthly': {'October': [54588.07]},
                                                  'weekly': {'2023-10-17 - 2023-10-23': [54588.07]}}),
             'Phoebe Yang': defaultdict(<class 'dict'>,
                                        {'daily': {'2023-10-25': [51390.0]},
                                         'monthly': {'October': [51390.0]},
                                         'weekly': {'2023-10-25 - 2023-10-31': [51390.0]}}),
             "Rhys D'Silva": defaultdict(<class 'dict'>,
                                         {'daily': {'2023-10-13': [20093.0]},
                                          'monthly': {'October': [20093.0]},
                                          'weekly': {'2023-10-13 - 2023-10-19': [20093.0]}}),
             'Richard Griffin': defaultdict(<class 'dict'>,
                                            {'daily': {'2023-10-13': [73184.25],
                                                       '2023-10-24': [41600.0],
                                                       '2023-10-26': [56886.19],
                                                       '2023-10-27': [25527.81]},
                                             'monthly': {'October': [73184.25,
                                                                     56886.19,
                                                                     41600.0,
                                                                     25527.81]},
                                             'weekly': {'2023-10-13 - 2023-10-19': [73184.25],
                                                        '2023-10-24 - 2023-10-30': [56886.19,
                                                                                    41600.0,
                                                                                    25527.81]}}),
             'Statewide Lending Pty Ltd': defaultdict(<class 'dict'>,
                                                      {'daily': {'2023-10-10': [15530.0]},
                                                       'monthly': {'October': [15530.0]},
                                                       'weekly': {'2023-10-10 - 2023-10-16': [15530.0]}}),
             'Steve Dahu': defaultdict(<class 'dict'>,
                                       {'daily': {'2023-10-17': [44390.0]},
                                        'monthly': {'October': [44390.0]},
                                        'weekly': {'2023-10-17 - 2023-10-23': [44390.0]}}),
             'Stratton Albury Wodonga': defaultdict(<class 'dict'>,
                                                    {'daily': {'2023-10-24': [32975.0]},
                                                     'monthly': {'October': [32975.0]},
                                                     'weekly': {'2023-10-24 - 2023-10-30': [32975.0]}}),
             'Stratton Clark': defaultdict(<class 'dict'>,
                                           {'daily': {'2023-10-25': [45188.0]},
                                            'monthly': {'October': [45188.0]},
                                            'weekly': {'2023-10-25 - 2023-10-31': [45188.0]}}),
             'Stratton Finance': defaultdict(<class 'dict'>,
                                             {'daily': {'2023-10-13': [66585.0],
                                                        '2023-10-24': [45707.2]},
                                              'monthly': {'October': [66585.0,
                                                                      45707.2]},
                                              'weekly': {'2023-10-13 - 2023-10-19': [66585.0],
                                                         '2023-10-24 - 2023-10-30': [45707.2]}}),
             'Stratton Finance Buderim': defaultdict(<class 'dict'>,
                                                     {'daily': {'2023-10-11': [53910.0]},
                                                      'monthly': {'October': [53910.0]},
                                                      'weekly': {'2023-10-11 - 2023-10-17': [53910.0]}}),
             'Stratton Finance Pty Ltd': defaultdict(<class 'dict'>,
                                                     {'daily': {'2023-10-25': [39100.0]},
                                                      'monthly': {'October': [39100.0]},
                                                      'weekly': {'2023-10-25 - 2023-10-31': [39100.0]}}),
             'Stratton Finance VIC': defaultdict(<class 'dict'>,
                                                 {'daily': {'2023-10-17': [45931.0],
                                                            '2023-10-25': [38200.46]},
                                                  'monthly': {'October': [45931.0,
                                                                          38200.46]},
                                                  'weekly': {'2023-10-17 - 2023-10-23': [45931.0],
                                                             '2023-10-25 - 2023-10-31': [38200.46]}}),
             'Stratton Norwest': defaultdict(<class 'dict'>,
                                             {'daily': {'2023-10-03': [36390.0],
                                                        '2023-10-04': [36390.0],
                                                        '2023-10-05': [76193.0],
                                                        '2023-10-10': [43890.0],
                                                        '2023-10-11': [55266.25,
                                                                       30490.0],
                                                        '2023-10-12': [77590.87],
                                                        '2023-10-17': [23244.74],
                                                        '2023-10-24': [51390.0],
                                                        '2023-10-25': [51774.35,
                                                                       34490.0],
                                                        '2023-10-27': [67535.7,
                                                                       65918.9,
                                                                       54572.04,
                                                                       47022.46]},
                                              'monthly': {'October': [77590.87,
                                                                      76193.0,
                                                                      67535.7,
                                                                      65918.9,
                                                                      55266.25,
                                                                      54572.04,
                                                                      51774.35,
                                                                      51390.0,
                                                                      47022.46,
                                                                      43890.0,
                                                                      36390.0,
                                                                      36390.0,
                                                                      34490.0,
                                                                      30490.0,
                                                                      23244.74]},
                                              'weekly': {'2023-10-03 - 2023-10-09': [76193.0,
                                                                                     36390.0,
                                                                                     36390.0],
                                                         '2023-10-10 - 2023-10-16': [77590.87,
                                                                                     55266.25,
                                                                                     43890.0,
                                                                                     30490.0],
                                                         '2023-10-17 - 2023-10-23': [23244.74],
                                                         '2023-10-24 - 2023-10-30': [67535.7,
                                                                                     65918.9,
                                                                                     54572.04,
                                                                                     51774.35,
                                                                                     51390.0,
                                                                                     47022.46,
                                                                                     34490.0]}}),
             'Stratton Wanneroo': defaultdict(<class 'dict'>,
                                              {'daily': {'2023-10-05': [81600.0]},
                                               'monthly': {'October': [81600.0]},
                                               'weekly': {'2023-10-05 - 2023-10-11': [81600.0]}}),
             'The Trustee for Smiffee Family Trust': defaultdict(<class 'dict'>,
                                                                 {'daily': {'2023-10-03': [89199.0]},
                                                                  'monthly': {'October': [89199.0]},
                                                                  'weekly': {'2023-10-03 - 2023-10-09': [89199.0]}}),
             'Tom Foster': defaultdict(<class 'dict'>,
                                       {'daily': {'2023-10-04': [36900.0]},
                                        'monthly': {'October': [36900.0]},
                                        'weekly': {'2023-10-04 - 2023-10-10': [36900.0]}}),
             'Trevor Wright': defaultdict(<class 'dict'>,
                                          {'daily': {'2023-10-17': [29900.0]},
                                           'monthly': {'October': [29900.0]},
                                           'weekly': {'2023-10-17 - 2023-10-23': [29900.0]}}),
             'Zac Biddiscombe': defaultdict(<class 'dict'>,
                                            {'daily': {'2023-10-23': [47719.15]},
                                             'monthly': {'October': [47719.15]},
                                             'weekly': {'2023-10-23 - 2023-10-29': [47719.15]}})})



Total loan amount report 

defaultdict(<class 'float'>,
            {'2023-10-02': 235696.06000000003,
             '2023-10-03': 153214.0,
             '2023-10-04': 172510.0,
             '2023-10-05': 304373.0,
             '2023-10-06': 130150.2,
             '2023-10-09': 274484.56000000006,
             '2023-10-10': 295420.05,
             '2023-10-11': 189056.25,
             '2023-10-12': 150537.37,
             '2023-10-13': 159862.25,
             '2023-10-16': 38770.0,
             '2023-10-17': 299991.92,
             '2023-10-18': 54342.99,
             '2023-10-23': 136091.49,
             '2023-10-24': 273312.12,
             '2023-10-25': 412601.88000000006,
             '2023-10-26': 161656.19,
             '2023-10-27': 405743.00999999995,
             '2023-10-30': 59933.81})



Tier level report 

defaultdict(<class 'dict'>,
            {'2023-10-02': {'tier1': 0, 'tier2': 2, 'tier3': 3},
             '2023-10-03': {'tier1': 0, 'tier2': 1, 'tier3': 2},
             '2023-10-04': {'tier1': 0, 'tier2': 1, 'tier3': 3},
             '2023-10-05': {'tier1': 0, 'tier2': 2, 'tier3': 4},
             '2023-10-06': {'tier1': 0, 'tier2': 1, 'tier3': 2},
             '2023-10-09': {'tier1': 0, 'tier2': 2, 'tier3': 4},
             '2023-10-10': {'tier1': 0, 'tier2': 4, 'tier3': 2},
             '2023-10-11': {'tier1': 0, 'tier2': 2, 'tier3': 2},
             '2023-10-12': {'tier1': 0, 'tier2': 2, 'tier3': 1},
             '2023-10-13': {'tier1': 0, 'tier2': 2, 'tier3': 1},
             '2023-10-16': {'tier1': 0, 'tier2': 0, 'tier3': 1},
             '2023-10-17': {'tier1': 0, 'tier2': 1, 'tier3': 7},
             '2023-10-18': {'tier1': 0, 'tier2': 1, 'tier3': 0},
             '2023-10-23': {'tier1': 0, 'tier2': 1, 'tier3': 2},
             '2023-10-24': {'tier1': 0, 'tier2': 2, 'tier3': 4},
             '2023-10-25': {'tier1': 0, 'tier2': 3, 'tier3': 6},
             '2023-10-26': {'tier1': 0, 'tier2': 1, 'tier3': 3},
             '2023-10-27': {'tier1': 0, 'tier2': 4, 'tier3': 4},
             '2023-10-30': {'tier1': 0, 'tier2': 1, 'tier3': 0}})
(env_transaction) ➜  pdfparser git:(feat_pdf_to_data_converter) ✗ 
```