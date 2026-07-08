"""
clean_data.py
-------------
Loads raw CSVs from data/raw/, cleans them, writes cleaned CSVs to data/cleaned/,
and writes a plain-text report of every issue found to output/data_quality_report.txt

Functions (as required by the assignment):
    clean_orders()              -> fix date formats, handle NULL customer_ids
    clean_products()             -> normalize product names (trim + title case)
    validate_emails()            -> list of customer_ids with invalid emails
    check_referential_integrity()-> order_items rows referencing non-existent orders
"""

import pandas as pd
import re
from datetime import datetime

RAW_DIR = "data/raw"
CLEAN_DIR = "data/cleaned"
REPORT_PATH = "output/data_quality_report.txt"

report_lines = []


def log(msg):
    """Collect a line for the final data quality report AND print it."""
    print(msg)
    report_lines.append(msg)


# ---------------------------------------------------------------------------
# 1. clean_orders
# ---------------------------------------------------------------------------
def clean_orders(orders_df):
    """
    - Standardizes order_date to YYYY-MM-DD HH:MM:SS (handles the DD-MM-YYYY variant)
    - customer_id: blank/whitespace -> NaN, keeps NaN as missing (does NOT invent an id --
      dropping the row would lose revenue and order data, so we keep the order but mark
      the customer as unknown; this is a decision worth explaining in an interview: we're
      choosing "keep + flag" over "drop", since these are still real orders/revenue)
    """
    df = orders_df.copy()

    # --- customer_id cleanup ---
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    df["customer_id"] = df["customer_id"].replace(["", "nan", "NULL", "None"], pd.NA)
    # Use pandas' nullable integer type (Int64, capital I) instead of plain int/float.
    # Plain int can't hold NaN at all, and float silently turns 265 into 265.0 the moment
    # a NaN is present in the column. Int64 keeps whole numbers whole AND supports <NA>.
    df["customer_id"] = df["customer_id"].astype("Int64")
    missing_customer_count = df["customer_id"].isna().sum()
    log(f"[clean_orders] Orders with missing customer_id: {missing_customer_count}")

    # --- order_date cleanup ---
    def parse_date(value):
        value = str(value).strip()
        # Try the correct format first
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return pd.NaT

    parsed = df["order_date"].apply(parse_date)
    bad_format_count = df["order_date"].apply(
        lambda v: bool(re.match(r"^\d{2}-\d{2}-\d{4}$", str(v).strip()))
    ).sum()
    unparseable_count = parsed.isna().sum()

    log(f"[clean_orders] Orders with DD-MM-YYYY format (fixed): {bad_format_count}")
    log(f"[clean_orders] Orders with unparseable order_date (set to NaT): {unparseable_count}")

    df["order_date"] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")

    # --- future-dated orders: flag, don't silently delete ---
    today = pd.Timestamp.now()
    future_mask = parsed > today
    log(f"[clean_orders] Orders with a future order_date (flagged, not removed): {future_mask.sum()}")

    # --- status normalization (defensive: uppercase + strip) ---
    df["status"] = df["status"].astype(str).str.strip().str.upper()

    return df


# ---------------------------------------------------------------------------
# 2. clean_products
# ---------------------------------------------------------------------------
def clean_products(products_df):
    """Trims whitespace and applies title case to product_name."""
    df = products_df.copy()

    before = df["product_name"].copy()
    df["product_name"] = df["product_name"].astype(str).str.strip().str.title()
    changed = (before != df["product_name"]).sum()
    log(f"[clean_products] Product names normalized (trimmed/title-cased): {changed}")

    # Also strip category/subcategory defensively
    df["category"] = df["category"].astype(str).str.strip()
    df["subcategory"] = df["subcategory"].astype(str).str.strip()

    return df


# ---------------------------------------------------------------------------
# 3. validate_emails
# ---------------------------------------------------------------------------
def validate_emails(customers_df):
    """
    Returns a list of customer_ids whose email is invalid.
    A valid email must have exactly one '@', a non-empty local part,
    and a domain part containing at least one '.'.
    """
    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    invalid_ids = []
    for _, row in customers_df.iterrows():
        email = str(row["email"]).strip()
        if not EMAIL_RE.match(email):
            invalid_ids.append(row["customer_id"])

    log(f"[validate_emails] Invalid emails found: {len(invalid_ids)}")
    return invalid_ids


# ---------------------------------------------------------------------------
# 4. check_referential_integrity
# ---------------------------------------------------------------------------
def check_referential_integrity(orders_df, order_items_df):
    """
    Returns the subset of order_items rows whose order_id does NOT exist in orders.
    """
    valid_order_ids = set(orders_df["order_id"])
    orphaned = order_items_df[~order_items_df["order_id"].isin(valid_order_ids)]

    log(f"[check_referential_integrity] Orphaned order_items rows (bad order_id): {len(orphaned)}")
    return orphaned


# ---------------------------------------------------------------------------
# Additional light validation (not required by name, but worth reporting)
# ---------------------------------------------------------------------------
def report_extra_issues(order_items_df):
    neg_qty = (order_items_df["quantity"] < 0).sum()
    zero_qty = (order_items_df["quantity"] == 0).sum()
    bad_discount = ((order_items_df["discount_percent"] < 0) |
                    (order_items_df["discount_percent"] > 100)).sum()

    log(f"[report_extra_issues] order_items with negative quantity (returns): {neg_qty}")
    log(f"[report_extra_issues] order_items with zero quantity: {zero_qty}")
    log(f"[report_extra_issues] order_items with discount_percent out of [0,100]: {bad_discount}")


def main():
    log("=" * 60)
    log("DATA QUALITY REPORT")
    log(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)

    orders = pd.read_csv(f"{RAW_DIR}/orders.csv", dtype={"customer_id": str})
    order_items = pd.read_csv(f"{RAW_DIR}/order_items.csv")
    products = pd.read_csv(f"{RAW_DIR}/products.csv")
    customers = pd.read_csv(f"{RAW_DIR}/customers.csv")

    orders_clean = clean_orders(orders)
    products_clean = clean_products(products)
    invalid_email_ids = validate_emails(customers)
    orphaned_items = check_referential_integrity(orders, order_items)
    report_extra_issues(order_items)

    # Drop orphaned order_items from the cleaned output (they can't be joined to anything)
    order_items_clean = order_items[~order_items.index.isin(orphaned_items.index)].copy()

    # customers.csv is passed through as-is (we report invalid emails, we don't silently
    # delete customers over a typo'd email -- that's a business decision, not a data bug)
    customers_clean = customers.copy()

    orders_clean.to_csv(f"{CLEAN_DIR}/orders_clean.csv", index=False)
    products_clean.to_csv(f"{CLEAN_DIR}/products_clean.csv", index=False)
    order_items_clean.to_csv(f"{CLEAN_DIR}/order_items_clean.csv", index=False)
    customers_clean.to_csv(f"{CLEAN_DIR}/customers_clean.csv", index=False)

    log("-" * 60)
    log(f"Customer IDs with invalid emails: {invalid_email_ids[:10]}"
        f"{' ...' if len(invalid_email_ids) > 10 else ''}")
    log("-" * 60)
    log("Cleaned files written to data/cleaned/")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\nReport saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
