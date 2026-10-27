# ☕ Makara Café POS (Python + Streamlit + SQLite)

A café point-of-sale demo designed for staff use, with separate **Admin** and **Cashier** permissions.

## Run on Mac
```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

## Demo accounts
- Admin: `admin` / `admin123`
- Cashier: `cashier` / `cashier123`

Change demo passwords before real business use. Admin can create and manage staff accounts in **Users & KHQR**. There is no customer login or public registration.

## Roles and permissions
| Page / action | Admin | Cashier |
|---|---:|---:|
| Dashboard | Full dashboard and 7-day chart | Dashboard |
| Create orders, calculate totals and issue receipts | ✅ | ✅ |
| View and update orders | All dates | Today's orders |
| View stock, add/remove stock and view stock log | ✅ | ✅ |
| Add/edit/delete products | ✅ | — |
| Sales reports (day/month, revenue/quantity, PDF and Excel) | ✅ | — |
| Create staff accounts, change passwords, delete staff accounts | ✅ | — |
| Configure KHQR merchant settings | ✅ | — |

## Payments
- **Cash**: enter amount received and show change.
- **KHQR**: app generates a KHQR image using the Bakong ID configured by Admin.
- **Photo QR (demo)**: optionally put a QR image in `Photo/`.

**Important:** KHQR payment confirmation is manual in this demo. Staff must verify payment in the banking app before confirming. The app does not independently verify that a bank transfer arrived.

## Order flow
Select products → adjust quantities → calculate total → choose payment method → confirm payment → save order and items, deduct stock, write stock log, and show receipt.

## Project structure
- `app.py` — Streamlit navigation and role-based pages
- `db.py` — SQLite schema, data access, products, orders and staff accounts
- `khqr.py` — KHQR payload builder
- `utils.py` — shared UI helpers, login checks, PDF/Excel receipts and reports
- `views/` — login, dashboard, order, stock, orders, reports and user/settings pages
- `style.css` — application styling
- `drinks.py` — product illustrations when no photo is uploaded
- `logo.svg` — sidebar logo

## Before selling or using with real customers
This is a demo-ready starting point, not yet a fully production-hardened commercial POS. Before deploying for a real business, replace demo credentials, use stronger password hashing, test database backups and recovery, verify payment status through a trusted payment integration if needed, and test access controls and order/stock handling thoroughly.
