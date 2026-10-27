"""Makara Café - entry point (router). Run:  python3 -m streamlit run app.py
Which pages appear in the sidebar depends on the user's role."""
import streamlit as st

import db
import utils

st.set_page_config(page_title="Mækařa Café", page_icon="☕", layout="wide")
db.init_db()


user = st.session_state.get("user")
P = st.Page

if not user:
    pg = st.navigation([P("views/login.py", title="Login", icon=":material/lock:")], position="hidden")
else:
    role = user["role"]
    dash = P("views/dashboard.py", title="Dashboard", icon=":material/dashboard:")
    order = P("views/order.py", title="Order", icon=":material/shopping_cart:", default=True)
    stock = P("views/stock.py", title="Stock", icon=":material/inventory_2:")
    orders = P("views/orders.py", title="Orders", icon=":material/receipt_long:")
    reports = P("views/reports.py", title="Reports", icon=":material/bar_chart:")
    users = P("views/users.py", title="Users & KHQR", icon=":material/settings:")
    pages = {
        "admin": [order, dash, stock, orders, reports, users],
        "cashier": [order, dash, stock, orders],
    }[role]
    pg = st.navigation(pages)
    with st.sidebar:
        st.write(f"👤 **{user['username']}** ({role})")
        if st.button("Logout", icon=":material/logout:"):
            st.session_state.clear()
            st.rerun()

utils.load_icons()
utils.load_css()
pg.run()
