"""
generate_data.py
-----------------
Generates 4 raw CSV files for the E-Commerce Order Analytics System:
    customers.csv, products.csv, orders.csv, order_items.csv

Intentional data quality issues (as required by the assignment):
    - 5% of orders have NULL customer_id
    - 3% of order_items have negative quantity (returns)
    - Some orders have order_date in wrong format (DD-MM-YYYY instead of YYYY-MM-DD HH:MM:SS)
    - Some product names have extra spaces / mixed case
    - 2% of emails are invalid (missing @ or domain)

No external libraries used except Python's standard library (random, csv, datetime).
This is deliberate — Faker isn't available in every environment, and stdlib random
gives full control over exactly which rows are "bad", which makes writing the
cleaning + test functions in Part 2/5 much easier to verify.
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)  # reproducible output — important so cleaning script results are stable

NUM_CUSTOMERS = 550
NUM_PRODUCTS = 520
NUM_ORDERS = 700
# order_items will end up >500 rows since each order has 1-4 items

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Sai", "Arjun", "Ishaan", "Ananya", "Diya",
               "Priya", "Kavya", "Riya", "Meera", "Rohan", "Karan", "Neha", "Pooja",
               "Amit", "Sanjay", "Deepak", "Ritu"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Reddy", "Nair",
              "Iyer", "Mehta", "Joshi", "Chopra", "Malhotra", "Kapoor", "Bansal"]

CATEGORIES = {
    "Electronics": ["Mobiles", "Laptops", "Headphones", "Cameras", "Accessories"],
    "Clothing": ["Men", "Women", "Kids", "Footwear"],
    "Home": ["Kitchen", "Furniture", "Decor", "Appliances"],
    "Books": ["Fiction", "Non-Fiction", "Academic", "Comics"],
}

PRODUCT_NAME_POOL = [
    "wireless mouse", "Bluetooth Speaker", "running shoes", "COTTON T-SHIRT",
    "office chair", "LED desk lamp", "notebook set", "steel water bottle",
    "gaming keyboard", "yoga mat", "kitchen knife set", "denim jacket",
    "smart watch", "coffee mug", "bookshelf", "wall clock", "backpack",
    "sunglasses", "table lamp", "phone case",
]

CUSTOMER_TYPES = ["REGULAR", "PREMIUM", "VIP"]
ORDER_STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
REGIONS = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]


def generate_customers(n):
    rows = []
    start_date = datetime(2023, 1, 1)
    for cid in range(1, n + 1):
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        name = f"{fname} {lname}"

        # 2% invalid emails: missing @ or missing domain
        roll = random.random()
        if roll < 0.01:
            email = f"{fname.lower()}{lname.lower()}gmail.com"          # missing @
        elif roll < 0.02:
            email = f"{fname.lower()}.{lname.lower()}@"                  # missing domain
        else:
            domain = random.choice(["gmail.com", "yahoo.com", "outlook.com"])
            email = f"{fname.lower()}.{lname.lower()}{cid}@{domain}"

        reg_date = start_date + timedelta(days=random.randint(0, 900))
        rows.append({
            "customer_id": cid,
            "customer_name": name,
            "email": email,
            "registration_date": reg_date.strftime("%Y-%m-%d"),
            "customer_type": random.choices(CUSTOMER_TYPES, weights=[0.6, 0.3, 0.1])[0],
        })
    return rows


def generate_products(n):
    rows = []
    for pid in range(1, n + 1):
        category = random.choice(list(CATEGORIES.keys()))
        subcategory = random.choice(CATEGORIES[category])
        base_name = random.choice(PRODUCT_NAME_POOL)

        # Intentional messiness: extra spaces / random casing on ~30% of rows
        name = base_name
        if random.random() < 0.3:
            name = f"  {name.upper()}  " if random.random() < 0.5 else f"{name.title()}   "

        cost_price = round(random.uniform(50, 5000), 2)
        rows.append({
            "product_id": pid,
            "product_name": name,
            "category": category,
            "subcategory": subcategory,
            "cost_price": cost_price,
        })
    return rows


def generate_orders(n, customer_ids):
    rows = []
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    span_days = (end_date - start_date).days

    for oid in range(1, n + 1):
        # 5% missing customer_id
        if random.random() < 0.05:
            customer_id = ""  # empty -> treated as NULL
        else:
            customer_id = random.choice(customer_ids)

        order_dt = start_date + timedelta(
            days=random.randint(0, span_days),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )

        # Some orders have wrong date format: DD-MM-YYYY (no time component)
        if random.random() < 0.1:
            order_date_str = order_dt.strftime("%d-%m-%Y")
        else:
            order_date_str = order_dt.strftime("%Y-%m-%d %H:%M:%S")

        rows.append({
            "order_id": oid,
            "customer_id": customer_id,
            "order_date": order_date_str,
            "status": random.choices(
                ORDER_STATUSES, weights=[0.15, 0.2, 0.45, 0.1, 0.1]
            )[0],
            "region_code": random.choice(REGIONS),
        })
    return rows


def generate_order_items(orders, product_ids):
    rows = []
    item_id = 1
    for order in orders:
        num_items = random.randint(1, 4)
        for _ in range(num_items):
            qty = random.randint(1, 5)
            # 3% negative quantity (returns)
            if random.random() < 0.03:
                qty = -qty

            unit_price = round(random.uniform(100, 8000), 2)
            discount = random.choice([0, 0, 0, 5, 10, 15, 20, 25, 30, 50])

            rows.append({
                "item_id": item_id,
                "order_id": order["order_id"],   # always references a real order_id
                "product_id": random.choice(product_ids),
                "quantity": qty,
                "unit_price": unit_price,
                "discount_percent": discount,
            })
            item_id += 1
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):>5} rows -> {path}")


def main():
    out_dir = "data/raw"

    customers = generate_customers(NUM_CUSTOMERS)
    customer_ids = [c["customer_id"] for c in customers]

    products = generate_products(NUM_PRODUCTS)
    product_ids = [p["product_id"] for p in products]

    orders = generate_orders(NUM_ORDERS, customer_ids)
    order_items = generate_order_items(orders, product_ids)

    write_csv(f"{out_dir}/customers.csv", customers,
              ["customer_id", "customer_name", "email", "registration_date", "customer_type"])
    write_csv(f"{out_dir}/products.csv", products,
              ["product_id", "product_name", "category", "subcategory", "cost_price"])
    write_csv(f"{out_dir}/orders.csv", orders,
              ["order_id", "customer_id", "order_date", "status", "region_code"])
    write_csv(f"{out_dir}/order_items.csv", order_items,
              ["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent"])

    print("\nDone. Note: order_items always reference a real order_id from orders.csv")
    print("by construction (each item is generated from an existing order object),")
    print("so referential integrity holds here by design. check_referential_integrity()")
    print("in clean_data.py still checks it properly — don't assume it's always true")
    print("for future data drops.")


if __name__ == "__main__":
    main()
