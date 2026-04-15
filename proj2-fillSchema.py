#!/usr/bin/env python3
"""
proj2-fillSchema.py
CS 4332 - Database Systems | Spring 2026
Caden

Generates and inserts sample data into the grocery store database.
Run proj2-makeSchema.sql first to create the empty tables.

Install dependencies:
    pip install psycopg2-binary faker python-dotenv
"""

import os
import random
import time
from datetime import datetime, timedelta, date

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from faker import Faker

# ── Config ─────────────────────────────────────────────────────────────────────

load_dotenv()

fake = Faker()
Faker.seed(42)
random.seed(42)

DB = {
    "host":     os.getenv("POSTGRES_HOST", "localhost"),
    "port":     int(os.getenv("POSTGRES_PORT", 5432)),
    "dbname":   os.getenv("POSTGRES_DB", "labdb"),
    "user":     os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

# ── DB helpers ─────────────────────────────────────────────────────────────────

def connect():
    return psycopg2.connect(**DB)

def wait_for_db(retries=10, delay=3):
    """Retry the connection a few times in case the container is still starting."""
    for attempt in range(1, retries + 1):
        try:
            conn = connect()
            conn.close()
            print("Connected to database.")
            return
        except psycopg2.OperationalError as e:
            print(f"Attempt {attempt}/{retries} — not ready yet. Retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError("Could not connect after multiple attempts. Is the container running?")

def already_seeded(conn):
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM "Store";')
        return cur.fetchone()[0] > 0

def insert(cur, table, columns, rows, page_size=500):
    """Bulk insert using execute_values for speed."""
    col_list = ", ".join(f'"{c}"' for c in columns)
    sql = f'INSERT INTO "{table}" ({col_list}) VALUES %s'
    execute_values(cur, sql, rows, page_size=page_size)
    print(f"  {len(rows):>6,} rows  →  {table}")

# ── Reference data ─────────────────────────────────────────────────────────────

CATEGORIES = [
    "Produce", "Meat", "Dairy", "Frozen",
    "Bakery", "Pantry", "Cleaning", "Beverages",
]

# Products grouped by category
PRODUCT_NAMES = {
    "Produce":   ["Apples", "Bananas", "Spinach", "Carrots", "Broccoli",
                  "Tomatoes", "Lettuce", "Onions", "Potatoes", "Strawberries"],
    "Meat":      ["Chicken Breast", "Ground Beef", "Pork Chops", "Salmon Fillet",
                  "Shrimp", "Bacon", "Turkey Breast", "Lamb Chops"],
    "Dairy":     ["Whole Milk", "2% Milk", "Cheddar Cheese", "Butter",
                  "Greek Yogurt", "Sour Cream", "Cream Cheese", "Mozzarella"],
    "Frozen":    ["Frozen Pizza", "Ice Cream", "Frozen Waffles", "Chicken Nuggets",
                  "Frozen Peas", "Fish Sticks", "Frozen Burritos"],
    "Bakery":    ["Sourdough Bread", "Bagels", "Croissants", "Blueberry Muffins",
                  "White Bread", "Dinner Rolls", "Cinnamon Rolls"],
    "Pantry":    ["Pasta", "Jasmine Rice", "Olive Oil", "Peanut Butter", "Granola",
                  "Canned Tomatoes", "Black Beans", "Rolled Oats", "Raw Honey"],
    "Cleaning":  ["Dish Soap", "Laundry Detergent", "Paper Towels",
                  "Trash Bags", "All-Purpose Cleaner", "Sponges"],
    "Beverages": ["Orange Juice", "Apple Juice", "Sparkling Water", "Ground Coffee",
                  "Green Tea", "Sports Drink", "Lemonade", "Coconut Water"],
}

BRANDS = [
    "Nature's Best", "FreshFarm", "HomeValue", "Sunrise", "Golden Harvest",
    "Meadow Fresh", "Peak Select", "Heritage", "Greenleaf", "Summit",
    "Clearspring", "Ridgeline",
]

SUPPLIER_NAMES = [
    "TexStar Distribution",   "Lone Star Fresh",        "Central Provisions Co.",
    "Hill Country Supply",    "Gulf Coast Foods",        "Prairie Wind Wholesale",
    "Red River Trading",      "Bluebonnet Fresh",        "Pinewood Distributors",
    "Alamo Food Group",       "Crossroads Supply",       "Harvest Moon Logistics",
]

TEXAS_CITIES = [
    ("San Marcos",  "TX", "78666"),
    ("Austin",      "TX", "78701"),
    ("Houston",     "TX", "77001"),
    ("Dallas",      "TX", "75201"),
    ("San Antonio", "TX", "78201"),
    ("Lubbock",     "TX", "79401"),
    ("El Paso",     "TX", "79901"),
]

NON_MANAGER_ROLES = ["Cashier", "Stocker", "Deli Clerk", "Bakery Clerk", "Produce Clerk"]

# ── Data generators ────────────────────────────────────────────────────────────

def gen_stores(n=5):
    cities = random.sample(TEXAS_CITIES, n)
    rows = []
    for store_num, (city, state, zip_code) in enumerate(cities, start=1):
        rows.append((
            store_num,
            fake.street_address(),
            city, state, zip_code,
            "Mon–Sat 7am–10pm, Sun 8am–9pm",
        ))
    return rows

def gen_suppliers():
    rows = []
    for sid, name in enumerate(SUPPLIER_NAMES, start=1):
        contact = f"{fake.name()} | {fake.phone_number()} | {fake.company_email()}"
        rows.append((sid, name, contact))
    return rows

def gen_categories():
    return [(i + 1, name) for i, name in enumerate(CATEGORIES)]

def gen_customers(n=300):
    rows = []
    for cid in range(1, n + 1):
        phone = fake.phone_number()[:20] if random.random() > 0.2 else None
        email = fake.unique.email()      if random.random() > 0.1 else None
        rows.append((cid, fake.first_name(), fake.last_name(), phone, email))
    return rows

def gen_employees(store_ids):
    rows = []
    eid = 1
    for store_id in store_ids:
        headcount = random.randint(4, 8)
        for j in range(headcount):
            # first employee at each store is always the store manager
            role  = "Store Manager" if j == 0 else random.choice(NON_MANAGER_ROLES)
            phone = fake.phone_number()[:20] if random.random() > 0.3 else None
            rows.append((eid, fake.first_name(), fake.last_name(), role, phone, store_id))
            eid += 1
    return rows

def gen_products(supplier_ids, category_map):
    rows = []
    pid = 1
    for cat_name, names in PRODUCT_NAMES.items():
        cat_id = category_map[cat_name]
        for name in names:
            brand       = random.choice(BRANDS)
            price       = round(random.uniform(0.99, 24.99), 2)
            supplier_id = random.choice(supplier_ids)
            sku         = f"SKU-{pid:05d}"
            rows.append((pid, name, brand, price, supplier_id, cat_id, sku))
            pid += 1
    return rows

def gen_store_hours(store_ids):
    rows = []
    for store_id in store_ids:
        for day in range(7):
            open_t  = "08:00" if day == 0 else "07:00"  # Sunday opens later
            close_t = "21:00" if day == 0 else "22:00"
            rows.append((store_id, day, open_t, close_t))
    return rows

def gen_inventory(store_ids, product_ids):
    rows = []
    for store_id in store_ids:
        # each store stocks about 80% of the product catalog
        stocked = random.sample(product_ids, int(len(product_ids) * 0.8))
        for pid in stocked:
            qty = random.randint(0, 200)
            rows.append((store_id, pid, qty))
    return rows

def gen_transactions(n, store_ids, customer_ids):
    rows = []
    start_date = datetime(2025, 1, 1)
    for sale_id in range(1, n + 1):
        store_id = random.choice(store_ids)
        # ~20% of checkouts are guests (no loyalty account)
        cid = random.choice(customer_ids) if random.random() > 0.2 else None
        dt  = start_date + timedelta(
            days    = random.randint(0, 450),
            hours   = random.randint(7, 21),
            minutes = random.randint(0, 59),
        )
        rows.append((sale_id, store_id, cid, dt))
    return rows

def gen_sale_items(transaction_ids, product_ids, price_map):
    rows = []
    for sale_id in transaction_ids:
        num_items = random.randint(1, 6)
        chosen    = random.sample(product_ids, min(num_items, len(product_ids)))
        for pid in chosen:
            qty   = random.randint(1, 5)
            # slight price variation simulates sales/markups over time
            price = round(price_map[pid] * random.uniform(0.9, 1.1), 2)
            rows.append((sale_id, pid, qty, price))
    return rows

def gen_restock_orders(n, store_ids, supplier_ids):
    rows = []
    start_date = date(2025, 1, 1)
    for order_id in range(1, n + 1):
        store_id    = random.choice(store_ids)
        supplier_id = random.choice(supplier_ids)
        delivery    = start_date + timedelta(days=random.randint(0, 450))
        rows.append((order_id, store_id, supplier_id, delivery))
    return rows

def gen_restock_details(order_ids, product_ids):
    rows = []
    for order_id in order_ids:
        num_products = random.randint(2, 8)
        chosen       = random.sample(product_ids, min(num_products, len(product_ids)))
        for pid in chosen:
            qty = random.randint(10, 500)
            rows.append((order_id, pid, qty))
    return rows

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    wait_for_db()
    conn = connect()

    try:
        with conn.cursor() as cur:
            if already_seeded(conn):
                print("Store table already has data — skipping seed.")
                print("Run proj2-makeSchema.sql first to reset the tables.")
                return

            print("\nSeeding...\n")

            # Root tables (no foreign keys)
            stores = gen_stores(5)
            insert(cur, "Store",
                   ["StoreNumber", "Street", "City", "State", "ZIP", "Hours"],
                   stores)
            cur.execute('SELECT "StoreID" FROM "Store" ORDER BY "StoreID";')
            store_ids = [r[0] for r in cur.fetchall()]

            suppliers = gen_suppliers()
            insert(cur, "Supplier", ["SupplierID", "Name", "Contact"], suppliers)
            supplier_ids = [s[0] for s in suppliers]

            categories = gen_categories()
            insert(cur, "Category", ["CategoryID", "Name"], categories)
            category_map = {name: cid for cid, name in categories}

            customers = gen_customers(300)
            insert(cur, "Customer",
                   ["CID", "FirstName", "LastName", "Phone", "Email"], customers)
            customer_ids = [c[0] for c in customers]

            # Level-1 dependents
            employees = gen_employees(store_ids)
            insert(cur, "Employee",
                   ["EID", "FirstName", "LastName", "Role", "Phone", "StoreID"], employees)

            products = gen_products(supplier_ids, category_map)
            insert(cur, "Product",
                   ["ProductID", "Name", "Brand", "Price", "SupplierID", "CategoryID", "SKU"],
                   products)
            product_ids = [p[0] for p in products]
            price_map   = {p[0]: p[3] for p in products}

            store_hours = gen_store_hours(store_ids)
            insert(cur, "StoreHours",
                   ["StoreID", "DayOfWeek", "OpenTime", "CloseTime"], store_hours)

            # Level-2 dependents
            inventory = gen_inventory(store_ids, product_ids)
            insert(cur, "Inventory", ["StoreID", "ProductID", "Quantity"], inventory)

            transactions = gen_transactions(2000, store_ids, customer_ids)
            insert(cur, "CustomerTransaction",
                   ["SaleID", "StoreID", "CID", "DateTime"], transactions)
            transaction_ids = [t[0] for t in transactions]

            restock_orders = gen_restock_orders(200, store_ids, supplier_ids)
            insert(cur, "RestockOrder",
                   ["OrderID", "StoreID", "SupplierID", "DeliveryDate"], restock_orders)
            order_ids = [o[0] for o in restock_orders]

            # Level-3 dependents
            sale_items = gen_sale_items(transaction_ids, product_ids, price_map)
            insert(cur, "SaleItem",
                   ["SaleID", "ProductID", "Quantity", "PriceAtTime"], sale_items)

            restock_details = gen_restock_details(order_ids, product_ids)
            insert(cur, "RestockDetail",
                   ["OrderID", "ProductID", "QuantityDelivered"], restock_details)

            conn.commit()
            print("\nDone.")

    except Exception as e:
        conn.rollback()
        print(f"\nRolled back. Error: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
