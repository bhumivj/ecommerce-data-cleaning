# E-Commerce Order Analytics System

End-to-end pipeline: generate messy raw data → clean it with pandas → load into SQLite →
run 16 SQL queries (basic through advanced window functions/CTEs) → CLI reporting tool.

## Architecture

```
ecommerce-analytics-system/
├── data/
│   ├── raw/            # generated, intentionally dirty CSVs
│   ├── cleaned/        # output of clean_data.py
│   └── ecommerce.db    # SQLite database (created by load_db.py)
├── scripts/
│   ├── generate_data.py    # Part 1: creates raw CSVs with intentional issues
│   ├── clean_data.py       # Part 2: cleaning functions + data quality report
│   ├── load_db.py          # loads cleaned CSVs into SQLite
│   ├── report_cli.py       # Part 4: CLI reporting tool
│   └── test_edge_cases.py  # Part 5: edge case tests
├── sql/
│   ├── schema.sql           # table definitions with PK/FK/CHECK constraints
│   ├── aggregations.sql     # queries 1-6 (basic + intermediate)
│   └── window_functions.sql # queries 7-16 (window functions, CTEs)
├── output/
│   ├── data_quality_report.txt
│   └── sample_reports/
└── README.md
```

## How to run (in order)

```bash
cd ecommerce-analytics-system

# 1. Generate raw data (550 customers, 520 products, 700 orders, ~1700 order_items)
python3 scripts/generate_data.py

# 2. Clean it, produce data/cleaned/*.csv + output/data_quality_report.txt
python3 scripts/clean_data.py

# 3. Load cleaned data into SQLite (data/ecommerce.db)
python3 scripts/load_db.py

# 4. Run the 16 SQL queries directly (optional, sanity check)
sqlite3 data/ecommerce.db < sql/aggregations.sql
sqlite3 data/ecommerce.db < sql/window_functions.sql

# 5. Run the CLI reporting tool
python3 scripts/report_cli.py --report monthly --start 2025-06-01 --end 2025-06-30
# or run with no args for an interactive prompt:
python3 scripts/report_cli.py

# 6. Run edge case tests
python3 scripts/test_edge_cases.py
```

Only dependency beyond the standard library is `pandas` (used in `generate_data.py`/
`clean_data.py`/`test_edge_cases.py` for cleaning logic). `report_cli.py` deliberately
uses **only** `sqlite3` + `argparse`, per the assignment's "no external libraries except
sqlite3" requirement for Part 4.

## Key design decisions (worth being able to explain out loud)

- **Missing customer_id**: kept as NULL, not dropped or defaulted to 0/-1. The order and
  its revenue are still real; deleting the row would understate revenue. NULL is the
  honest representation of "we don't know."
- **customer_id dtype bug**: pandas silently upcasts an int column to float the moment it
  contains a NaN (`265` becomes `265.0`). Fixed by using pandas' nullable `Int64` dtype
  instead of plain `int`/`float`.
- **Referential integrity**: order_items rows with an order_id not present in orders are
  detected by `check_referential_integrity()` and **dropped** from the cleaned dataset —
  they can't be joined to anything and would silently corrupt every revenue query.
- **Negative quantity**: NOT treated as bad data — it's the assignment's defined
  representation of a return, and is used directly in the "products with more returns
  than purchases" and "return rate per category" queries.
- **Future order_date**: flagged in the quality report, never silently deleted or
  "corrected" — a human should decide if it's a timezone bug or legitimate pre-order data.
- **Month-wise "last 12 months" query**: computed relative to `MAX(order_date)` in the
  dataset, not the real wall-clock date, since this is synthetic historical data with no
  relationship to today's date.
- **DENSE_RANK vs RANK** (query 8): the assignment explicitly requires tied revenue to
  produce the same rank with no gap afterward — that's DENSE_RANK's defined behavior,
  RANK would leave gaps.

## Known limitations

- `generate_data.py` builds order_items directly from in-memory order objects, so in this
  particular run every order_id in order_items is valid by construction. The referential
  integrity check and its edge case test are still real and independently verified against
  a synthetic bad row (see `test_edge_cases.py`) — don't assume future data drops will be this clean.
- Cohort analysis (query 15) defines "month 0" as the customer's registration month, and
  retention as "did they place ANY order in that relative month" — a simplification of
  true cohort/retention modeling, which in production would also weight repeat purchase
  frequency and revenue, not just presence/absence.
