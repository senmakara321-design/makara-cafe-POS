"""Database layer (SQLite). Every page talks to the database only through this file."""
import hashlib
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "makara.db"
LOW_STOCK = 10  # warn when stock <= this number
DEFAULT_BAKONG_ID = "makara@demo"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL  -- admin | cashier
);
CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    category TEXT NOT NULL DEFAULT 'Other',
    active INTEGER NOT NULL DEFAULT 1,
    image TEXT,
    description TEXT
);
CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    total REAL NOT NULL,
    cashier TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Paid',   -- Paid | Pending | Cancelled
    customer TEXT
);
CREATE TABLE IF NOT EXISTS order_items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    qty INTEGER NOT NULL,
    price REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS stock_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    change INTEGER NOT NULL,
    reason TEXT,
    date TEXT NOT NULL,
    user TEXT NOT NULL
);
"""

SAMPLE_PRODUCTS = [
    ("Iced Coffee", 2.00, 50, "Coffee"), ("Hot Coffee", 1.75, 50, "Coffee"),
    ("Latte", 2.75, 40, "Coffee"), ("Cappuccino", 2.75, 40, "Coffee"),
    ("Green Tea", 2.00, 40, "Tea"), ("Milk Tea", 2.25, 40, "Tea"),
    ("Mango Smoothie", 3.00, 30, "Smoothie"), ("Strawberry Smoothie", 3.00, 30, "Smoothie"),
    ("Croissant", 2.00, 25, "Bakery"), ("Chocolate Cake", 3.50, 15, "Bakery"),
    ("Cheesecake", 3.50, 15, "Bakery"), ("Mineral Water", 0.50, 100, "Other"),
]


SAMPLE_DESC = {
    "Iced Coffee": "Cold brew over ice, smooth and refreshing", "Hot Coffee": "Freshly brewed black coffee, served hot",
    "Latte": "Espresso with steamed milk and a light foam", "Cappuccino": "Espresso, steamed milk and thick milk foam",
    "Green Tea": "Fragrant green tea leaves, lightly sweet", "Milk Tea": "Classic milk tea with chewy tapioca pearls",
    "Mango Smoothie": "Ripe mango blended with ice and milk", "Strawberry Smoothie": "Fresh strawberries blended with yogurt",
    "Croissant": "Buttery, flaky and baked fresh every morning", "Chocolate Cake": "Rich chocolate sponge with cocoa frosting",
    "Cheesecake": "Creamy cheesecake with strawberry glaze", "Mineral Water": "Chilled natural mineral water 500ml",
}


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _migrate(conn):
    """Upgrade a database made by the first version of the project."""
    row = conn.execute("SELECT sql FROM sqlite_master WHERE name='users'").fetchone()
    if row and "CHECK" in row[0]:  # old users table only allowed admin/cashier
        conn.executescript("""
            ALTER TABLE users RENAME TO users_old;
            CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
                               password TEXT NOT NULL, role TEXT NOT NULL);
            INSERT INTO users(id,username,password,role) SELECT id,username,password,role FROM users_old;
            DROP TABLE users_old;""")
    pcols = [r["name"] for r in conn.execute("PRAGMA table_info(products)")]
    if "description" not in pcols:
        conn.execute("ALTER TABLE products ADD COLUMN description TEXT")
    if "image" not in pcols:
        conn.execute("ALTER TABLE products ADD COLUMN image TEXT")
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(orders)")]
    if "status" not in cols:
        conn.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'Paid'")
    if "customer" not in cols:
        conn.execute("ALTER TABLE orders ADD COLUMN customer TEXT")
    conn.commit()


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    _migrate(conn)
    # Remove legacy customer accounts before checking whether staff accounts need seeding.
    # Existing order history is preserved.
    conn.execute("DELETE FROM users WHERE role NOT IN ('admin', 'cashier')")
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO users(username,password,role) VALUES(?,?,?)",
            [("admin", hash_pw("admin123"), "admin"), ("cashier", hash_pw("cashier123"), "cashier")],
        )
    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        conn.executemany("INSERT INTO products(name,price,stock,category) VALUES(?,?,?,?)", SAMPLE_PRODUCTS)
    for n, d in SAMPLE_DESC.items():  # give the demo menu a description (only if none yet)
        conn.execute("UPDATE products SET description=? WHERE name=? AND description IS NULL", (d, n))
    conn.commit()
    conn.close()


def _df(sql, params=()):
    conn = get_conn()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


# ---------------- users ----------------
def login(username, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT id, username, role FROM users WHERE username=? AND password=? AND role IN ('admin', 'cashier')",
        (username, hash_pw(password)),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------- products & stock ----------------
def list_products():
    return _df("SELECT id, name, price, stock, category, image, description FROM products WHERE active=1 ORDER BY category, name")


def add_product(name, price, stock, category, user, image=None, description=""):
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO products(name,price,stock,category,image,description) VALUES(?,?,?,?,?,?)",
            (name.strip(), float(price), int(stock), category.strip() or "Other", image, (description or "").strip()),
        )
        if stock:
            conn.execute(
                "INSERT INTO stock_log(product_id,change,reason,date,user) VALUES(?,?,?,?,?)",
                (cur.lastrowid, int(stock), "New product", now(), user),
            )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"Product '{name}' already exists")
    finally:
        conn.close()


def update_product(pid, name, price, category, image=None, description=None):
    """image=None keeps the current photo, image='' removes it, image='abc.jpg' sets a new one."""
    conn = get_conn()
    try:
        conn.execute("UPDATE products SET name=?, price=?, category=? WHERE id=?",
                     (name.strip(), float(price), category.strip() or "Other", pid))
        if image is not None:
            conn.execute("UPDATE products SET image=? WHERE id=?", (image or None, pid))
        if description is not None:
            conn.execute("UPDATE products SET description=? WHERE id=?", (description.strip(), pid))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"Another product is already named '{name}'")
    finally:
        conn.close()


def delete_product(pid):
    """Soft delete: hide the product but keep old orders/reports intact."""
    conn = get_conn()
    conn.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def adjust_stock(pid, change, reason, user):
    """change > 0 adds stock, change < 0 removes stock (never below 0)."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT stock FROM products WHERE id=?", (pid,)).fetchone()
        if row is None:
            raise ValueError("Product not found")
        if row["stock"] + change < 0:
            raise ValueError(f"Cannot remove {-change}: only {row['stock']} in stock")
        conn.execute("UPDATE products SET stock = stock + ? WHERE id=?", (change, pid))
        conn.execute(
            "INSERT INTO stock_log(product_id,change,reason,date,user) VALUES(?,?,?,?,?)",
            (pid, change, reason or ("Add stock" if change > 0 else "Remove stock"), now(), user),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def stock_log(limit=200):
    return _df(
        """SELECT l.date AS Date, p.name AS Product, l.change AS Change, l.reason AS Reason, l.user AS User
           FROM stock_log l JOIN products p ON p.id = l.product_id ORDER BY l.id DESC LIMIT ?""",
        (limit,),
    )


# ---------------- orders ----------------
def create_order(cart, cashier, payment_method, when=None, status="Paid", customer=None):
    """cart = {product_id: qty}. Checks stock, saves order, cuts stock, writes stock log.
    Everything happens in ONE transaction: all succeed or nothing is saved."""
    if not cart:
        raise ValueError("Cart is empty")
    conn = get_conn()
    try:
        lines, total = [], 0.0
        for pid, qty in cart.items():
            p = conn.execute("SELECT * FROM products WHERE id=? AND active=1", (pid,)).fetchone()
            if p is None:
                raise ValueError("A product in the cart no longer exists")
            if p["stock"] < qty:
                raise ValueError(f"Not enough stock for {p['name']} (only {p['stock']} left)")
            lines.append((p, qty))
            total += p["price"] * qty
        when = when or now()
        oid = conn.execute(
            "INSERT INTO orders(date,total,cashier,payment_method,status,customer) VALUES(?,?,?,?,?,?)",
            (when, round(total, 2), cashier, payment_method, status, customer),
        ).lastrowid
        for p, qty in lines:
            conn.execute("INSERT INTO order_items(order_id,product_id,qty,price) VALUES(?,?,?,?)",
                         (oid, p["id"], qty, p["price"]))
            conn.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, p["id"]))
            conn.execute("INSERT INTO stock_log(product_id,change,reason,date,user) VALUES(?,?,?,?,?)",
                         (p["id"], -qty, f"Sale #{oid}", when, cashier))
        conn.commit()
        return oid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_orders(start, end, customer=None, status=None):
    sql = """SELECT id AS Order_ID, date AS Date, total AS Total, cashier AS Cashier,
                    COALESCE(customer,'') AS Customer, payment_method AS Payment, status AS Status
             FROM orders WHERE substr(date,1,10) BETWEEN ? AND ?"""
    params = [str(start), str(end)]
    if customer:
        sql += " AND customer=?"; params.append(customer)
    if status:
        sql += " AND status=?"; params.append(status)
    return _df(sql + " ORDER BY id DESC", params)


def pending_orders():
    return _df("""SELECT id AS Order_ID, date AS Date, total AS Total, COALESCE(customer,'') AS Customer
                  FROM orders WHERE status='Pending' ORDER BY id""")


def set_order_status(oid, new_status, user):
    """Only Pending orders can change. Cancelled -> stock goes back to the shelf."""
    conn = get_conn()
    try:
        o = conn.execute("SELECT status FROM orders WHERE id=?", (oid,)).fetchone()
        if o is None or o["status"] != "Pending":
            raise ValueError("Only Pending orders can be changed")
        if new_status == "Paid":
            conn.execute("UPDATE orders SET status='Paid', payment_method='Cash', cashier=? WHERE id=?", (user, oid))
        elif new_status == "Cancelled":
            conn.execute("UPDATE orders SET status='Cancelled' WHERE id=?", (oid,))
            for it in conn.execute("SELECT product_id, qty FROM order_items WHERE order_id=?", (oid,)).fetchall():
                conn.execute("UPDATE products SET stock = stock + ? WHERE id=?", (it["qty"], it["product_id"]))
                conn.execute("INSERT INTO stock_log(product_id,change,reason,date,user) VALUES(?,?,?,?,?)",
                             (it["product_id"], it["qty"], f"Cancel #{oid}", now(), user))
        else:
            raise ValueError("Unknown status")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_order(oid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_order_items(oid):
    return _df(
        """SELECT p.name AS Product, oi.qty AS Qty, oi.price AS Price, oi.qty*oi.price AS Amount
           FROM order_items oi JOIN products p ON p.id = oi.product_id WHERE oi.order_id=?""",
        (oid,),
    )


# ---------------- reports ----------------
def _plen(period):
    return 7 if period == "month" else 10  # 'YYYY-MM' or 'YYYY-MM-DD'


def sales_by_period(period, start, end):
    n = _plen(period)
    return _df(
        f"""SELECT substr(date,1,{n}) AS Period, COUNT(*) AS Orders, ROUND(SUM(total),2) AS Revenue
            FROM orders WHERE status='Paid' AND substr(date,1,10) BETWEEN ? AND ? GROUP BY Period ORDER BY Period""",
        (str(start), str(end)),
    )


def product_sales(start, end):
    return _df(
        """SELECT p.name AS Product, SUM(oi.qty) AS Qty_Sold, ROUND(SUM(oi.qty*oi.price),2) AS Revenue
           FROM order_items oi JOIN orders o ON o.id = oi.order_id JOIN products p ON p.id = oi.product_id
           WHERE o.status='Paid' AND substr(o.date,1,10) BETWEEN ? AND ? GROUP BY p.name ORDER BY Revenue DESC""",
        (str(start), str(end)),
    )


def product_sales_by_period(period, start, end):
    n = _plen(period)
    return _df(
        f"""SELECT substr(o.date,1,{n}) AS Period, p.name AS Product, SUM(oi.qty) AS Qty_Sold,
                   ROUND(SUM(oi.qty*oi.price),2) AS Revenue
            FROM order_items oi JOIN orders o ON o.id = oi.order_id JOIN products p ON p.id = oi.product_id
            WHERE o.status='Paid' AND substr(o.date,1,10) BETWEEN ? AND ? GROUP BY Period, p.name ORDER BY Period""",
        (str(start), str(end)),
    )


def seed_demo_sales(days=30, seed=1):
    """Insert random past orders so reports look alive in a demo (does not touch stock)."""
    rnd = random.Random(seed)
    prods = list_products().to_dict("records")
    conn = get_conn()
    for d in range(days, 0, -1):
        day = datetime.now() - timedelta(days=d)
        for _ in range(rnd.randint(4, 12)):
            when = day.replace(hour=rnd.randint(7, 20), minute=rnd.randint(0, 59), second=0).strftime("%Y-%m-%d %H:%M:%S")
            items = rnd.sample(prods, rnd.randint(1, 3))
            lines = [(p, rnd.randint(1, 3)) for p in items]
            total = sum(p["price"] * q for p, q in lines)
            oid = conn.execute("INSERT INTO orders(date,total,cashier,payment_method) VALUES(?,?,?,?)",
                               (when, round(total, 2), rnd.choice(["cashier", "admin"]),
                                rnd.choice(["Cash", "ABA QR"]))).lastrowid
            conn.executemany("INSERT INTO order_items(order_id,product_id,qty,price) VALUES(?,?,?,?)",
                             [(oid, p["id"], q, p["price"]) for p, q in lines])
    conn.commit()
    conn.close()


# ---------------- users ----------------
import re

ROLES = ("admin", "cashier")


def _check_credentials(username, password):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,20}", username or ""):
        raise ValueError("Username: 3-20 letters/numbers (_ . - allowed), no spaces")
    if len(password or "") < 4:
        raise ValueError("Password must be at least 4 characters")


def create_user(username, password, role):
    username = (username or "").strip()
    _check_credentials(username, password)
    if role not in ROLES:
        raise ValueError("Unknown role")
    conn = get_conn()
    try:
        conn.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)", (username, hash_pw(password), role))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"Username '{username}' is already taken")
    finally:
        conn.close()


def list_users():
    return _df("SELECT id, username, role FROM users ORDER BY role, username")


def set_password(uid, password):
    if len(password or "") < 4:
        raise ValueError("Password must be at least 4 characters")
    conn = get_conn()
    conn.execute("UPDATE users SET password=? WHERE id=?", (hash_pw(password), uid))
    conn.commit()
    conn.close()


def delete_user(uid, acting_username):
    conn = get_conn()
    try:
        u = conn.execute("SELECT username, role FROM users WHERE id=?", (uid,)).fetchone()
        if u is None:
            raise ValueError("User not found")
        if u["username"] == acting_username:
            raise ValueError("You cannot delete your own account")
        if u["role"] == "admin" and conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0] <= 1:
            raise ValueError("Cannot delete the last admin")
        conn.execute("DELETE FROM users WHERE id=?", (uid,))
        conn.commit()
    finally:
        conn.close()


# ---------------- settings (KHQR info etc.) ----------------
def get_setting(key, default=""):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_conn()
    conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    conn.commit()
    conn.close()
