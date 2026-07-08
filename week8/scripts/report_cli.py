"""
report_cli.py
-------------
Command-line reporting tool. No external libraries except sqlite3
(as required by the assignment -- so no tabulate/argparse-only-is-fine
since argparse is standard library, but table formatting is done by hand).

Usage (interactive):
    python3 report_cli.py

Usage (non-interactive, via CLI args):
    python3 report_cli.py --report daily   --start 2025-06-01 --end 2025-06-30
    python3 report_cli.py --report weekly  --start 2025-06-01 --end 2025-06-07
    python3 report_cli.py --report monthly --start 2025-06-01 --end 2025-06-30
"""

import sqlite3
import sys
import argparse
from datetime import datetime, timedelta

DB_PATH = "data/ecommerce.db"


def parse_date(s):
    """Validate a YYYY-MM-DD date string. Returns None if invalid."""
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d")
    except ValueError:
        return None


def get_period_dates():
    """Interactive prompt path: ask for report type + date range, with input validation."""
    while True:
        report_type = input("Report type (daily/weekly/monthly): ").strip().lower()
        if report_type in ("daily", "weekly", "monthly"):
            break
        print("Invalid report type. Please enter daily, weekly, or monthly.")

    while True:
        start_str = input("Start date (YYYY-MM-DD): ").strip()
        start_dt = parse_date(start_str)
        if start_dt:
            break
        print("Invalid date format. Use YYYY-MM-DD.")

    while True:
        end_str = input("End date (YYYY-MM-DD): ").strip()
        end_dt = parse_date(end_str)
        if end_dt and end_dt >= start_dt:
            break
        print("Invalid date, or end date is before start date. Try again.")

    return report_type, start_dt, end_dt


def previous_period(start_dt, end_dt):
    """Same-length window immediately preceding [start_dt, end_dt]."""
    span = (end_dt - start_dt) + timedelta(days=1)  # inclusive day count
    prev_end = start_dt - timedelta(days=1)
    prev_start = prev_end - span + timedelta(days=1)
    return prev_start, prev_end


def fetch_summary(conn, start_dt, end_dt):
    start_s = start_dt.strftime("%Y-%m-%d 00:00:00")
    end_s = end_dt.strftime("%Y-%m-%d 23:59:59")

    row = conn.execute("""
        SELECT
            COUNT(DISTINCT o.order_id)   AS total_orders,
            COUNT(DISTINCT o.customer_id) AS unique_customers,
            COALESCE(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 0) AS revenue
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.order_date BETWEEN ? AND ?
    """, (start_s, end_s)).fetchone()

    return {"total_orders": row[0], "unique_customers": row[1], "revenue": row[2] or 0.0}


def fetch_top_products(conn, start_dt, end_dt, limit=3):
    start_s = start_dt.strftime("%Y-%m-%d 00:00:00")
    end_s = end_dt.strftime("%Y-%m-%d 23:59:59")

    rows = conn.execute("""
        SELECT
            p.product_name,
            ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS revenue
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.order_date BETWEEN ? AND ?
        GROUP BY p.product_id, p.product_name
        ORDER BY revenue DESC
        LIMIT ?
    """, (start_s, end_s, limit)).fetchall()

    return rows


def pct_change(new, old):
    if old in (0, None):
        return None
    return round((new - old) / old * 100, 2)


def print_table(headers, rows):
    """Minimal hand-rolled table printer -- no tabulate allowed."""
    widths = [len(h) for h in headers]
    str_rows = [[str(c) for c in r] for r in rows]
    for r in str_rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(c))

    def fmt_row(cells):
        return " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells))

    print(fmt_row(headers))
    print("-+-".join("-" * w for w in widths))
    for r in str_rows:
        print(fmt_row(r))


def generate_report(conn, report_type, start_dt, end_dt):
    print("\n" + "=" * 60)
    print(f"{report_type.upper()} REPORT: {start_dt.date()} to {end_dt.date()}")
    print("=" * 60)

    summary = fetch_summary(conn, start_dt, end_dt)
    print(f"Total Orders     : {summary['total_orders']}")
    print(f"Total Revenue    : {summary['revenue']:.2f}")
    print(f"Unique Customers : {summary['unique_customers']}")

    print("\nTop 3 Products:")
    top_products = fetch_top_products(conn, start_dt, end_dt, limit=3)
    if top_products:
        print_table(["Product", "Revenue"], top_products)
    else:
        print("  (no orders in this period)")

    prev_start, prev_end = previous_period(start_dt, end_dt)
    prev_summary = fetch_summary(conn, prev_start, prev_end)

    print(f"\nComparison with previous period ({prev_start.date()} to {prev_end.date()}):")
    order_change = pct_change(summary["total_orders"], prev_summary["total_orders"])
    revenue_change = pct_change(summary["revenue"], prev_summary["revenue"])
    customer_change = pct_change(summary["unique_customers"], prev_summary["unique_customers"])

    def fmt_change(v):
        return "N/A (no prior data)" if v is None else f"{v:+.2f}%"

    print(f"  Orders    : {prev_summary['total_orders']} -> {summary['total_orders']}  ({fmt_change(order_change)})")
    print(f"  Revenue   : {prev_summary['revenue']:.2f} -> {summary['revenue']:.2f}  ({fmt_change(revenue_change)})")
    print(f"  Customers : {prev_summary['unique_customers']} -> {summary['unique_customers']}  ({fmt_change(customer_change)})")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="E-Commerce order analytics CLI reporting tool")
    parser.add_argument("--report", choices=["daily", "weekly", "monthly"], help="Report type")
    parser.add_argument("--start", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    args = parser.parse_args()

    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        print(f"Could not connect to database at {DB_PATH}: {e}")
        sys.exit(1)

    if args.report and args.start and args.end:
        start_dt = parse_date(args.start)
        end_dt = parse_date(args.end)
        if not start_dt or not end_dt or end_dt < start_dt:
            print("Invalid --start/--end date range.")
            sys.exit(1)
        report_type = args.report
    else:
        report_type, start_dt, end_dt = get_period_dates()

    try:
        generate_report(conn, report_type, start_dt, end_dt)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
