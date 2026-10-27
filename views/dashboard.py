"""Dashboard for admin + cashier."""
from datetime import date, timedelta

import streamlit as st

import db
import utils

user = utils.require_login(["admin", "cashier"])
utils.title("mug-hot", "Makara Café - Dashboard")
st.write(f"Welcome, **{user['username']}** ({user['role']}).")

today = date.today()
t = db.sales_by_period("day", today, today)
revenue = float(t["Revenue"].sum()) if not t.empty else 0.0
orders = int(t["Orders"].sum()) if not t.empty else 0
products = db.list_products()
low = products[products["stock"] <= db.LOW_STOCK]

c1, c2, c3 = st.columns(3)
c1.metric("Today's revenue", f"${revenue:,.2f}")
c2.metric("Today's paid orders", orders)
c3.metric("Low-stock items", len(low))

if not low.empty:
    st.warning("⚠️ Low stock: " + ", ".join(f"{r['name']} ({r['stock']})" for _, r in low.iterrows()))

if user["role"] == "admin":
    st.subheader("Revenue - last 7 days")
    w = db.sales_by_period("day", today - timedelta(days=6), today)
    if w.empty:
        st.info("No sales yet. Open Reports to load demo data, or create an order.")
    else:
        st.bar_chart(w.set_index("Period")["Revenue"])
