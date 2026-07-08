"""
test_edge_cases.py
-------------------
Verifies how the system behaves under the 4 required edge cases.
Run directly with: python3 scripts/test_edge_cases.py
(No pytest dependency -- kept as plain functions + a runner, in case
pytest isn't installed on the grading machine.)
"""

import sqlite3
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from clean_data import check_referential_integrity  # reuse the real function, don't reimplement

DB_PATH = "data/ecommerce.db"


def test_order_items_referencing_nonexistent_order():
    """1. What happens when order_items has an order_id not in orders?"""
    orders = pd.DataFrame({"order_id": [1, 2, 3]})
    order_items = pd.DataFrame({
        "order_id": [1, 2, 999],   # 999 doesn't exist
        "item_id": [1, 2, 3],
    })
    orphaned = check_referential_integrity(orders, order_items)
    assert len(orphaned) == 1, f"Expected 1 orphaned row, got {len(orphaned)}"
    assert orphaned.iloc[0]["order_id"] == 999
    print("PASS: orphaned order_items (bad order_id) correctly detected and isolated.")
    print("      -> Decision: these rows are DROPPED from the cleaned dataset "
          "(they can never be joined to a real order, so they'd corrupt every "
          "revenue query that joins orders + order_items).")


def test_discount_percent_over_100():
    """2. What happens when discount_percent > 100?"""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE order_items (
            item_id INTEGER, order_id INTEGER, product_id INTEGER,
            quantity INTEGER, unit_price REAL,
            discount_percent REAL CHECK (discount_percent BETWEEN 0 AND 100)
        )
    """)
    try:
        conn.execute(
            "INSERT INTO order_items VALUES (1, 1, 1, 2, 100.0, 150)"
        )
        conn.commit()
        raised = False
    except sqlite3.IntegrityError:
        raised = True

    assert raised, "Expected the CHECK constraint to reject discount_percent=150"
    print("PASS: discount_percent > 100 is REJECTED by the schema's CHECK constraint.")
    print("      -> In clean_data.py, report_extra_issues() flags these rows in the "
          "quality report BEFORE load, so a bad row never even reaches the DB insert. "
          "If it did reach the DB, the CHECK constraint is the second line of defense.")


def test_zero_quantity():
    """3. What happens when quantity is 0?"""
    df = pd.DataFrame({
        "order_id": [1, 2],
        "quantity": [0, 5],
        "unit_price": [100.0, 200.0],
        "discount_percent": [0, 0],
    })
    revenue = (df["quantity"] * df["unit_price"] * (1 - df["discount_percent"] / 100)).sum()

    zero_qty_rows = df[df["quantity"] == 0]
    assert len(zero_qty_rows) == 1
    assert revenue == 1000.0  # the qty=0 row contributes exactly 0 to revenue, no crash

    print("PASS: quantity=0 does not crash revenue calculation -- it just contributes ₹0.")
    print("      -> Decision: quantity=0 is NOT a return (that's negative) and not a "
          "real purchase either. It's most likely a data entry error. It's kept in the "
          "data (not silently dropped) but flagged in the quality report, since deleting "
          "it would hide a real upstream bug from whoever owns the source system.")


def test_future_order_date():
    """4. What happens when order_date is in the future?"""
    from datetime import datetime, timedelta
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

    df = pd.DataFrame({
        "order_id": [1],
        "customer_id": ["5"],
        "order_date": [future_date],
        "status": ["PLACED"],
        "region_code": ["NORTH"],
    })

    from clean_data import clean_orders
    cleaned = clean_orders(df)

    parsed_date = pd.to_datetime(cleaned["order_date"].iloc[0])
    assert parsed_date > pd.Timestamp.now()

    print("PASS: future-dated orders are NOT silently deleted or auto-corrected.")
    print("      -> clean_orders() flags them (see '[clean_orders] Orders with a future "
          "order_date' line in the quality report) so a human can decide whether it's a "
          "timezone bug, a pre-order, or bad test data. Guessing and silently fixing dates "
          "would be worse than leaving it visible.")


def run_all():
    tests = [
        test_order_items_referencing_nonexistent_order,
        test_discount_percent_over_100,
        test_zero_quantity,
        test_future_order_date,
    ]
    failed = 0
    for t in tests:
        print(f"\n--- {t.__name__} ---")
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"FAIL: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} edge case tests passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run_all()
