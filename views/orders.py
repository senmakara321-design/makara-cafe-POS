"""Staff: view orders and download receipts."""
from datetime import date

import streamlit as st

import db
import utils

user = utils.require_login(["admin", "cashier"])
utils.title("receipt", "Orders")
utils.show_flash()

st.subheader("All orders")
if user["role"] == "admin":
    c1, c2 = st.columns(2)
    start = c1.date_input("From", date.today())
    end = c2.date_input("To", date.today())
else:
    start = end = date.today()
    st.caption("Cashier view: today's orders only.")

orders = db.get_orders(start, end)
if orders.empty:
    st.info("No orders in this period.")
    st.stop()

paid = orders[orders["Status"] == "Paid"]
st.metric("Paid total", f"${paid['Total'].sum():,.2f}", f"{len(paid)} paid orders")
st.dataframe(orders, hide_index=True, width="stretch")

oid = st.selectbox("Open order", orders["Order_ID"].tolist())
order = db.get_order(int(oid))
items = db.get_order_items(int(oid))
st.write(f"**Order #{oid}** • {order['date']} • {order['cashier']} • {order['payment_method']} • {order['status']}")
st.dataframe(items, hide_index=True)
st.write(f"**Total: ${order['total']:.2f}**")
if order["status"] == "Paid":
    d1, d2, _ = st.columns([1, 1, 3])
    d1.download_button("⬇️ PDF", utils.receipt_pdf(order, items), f"receipt_{oid}.pdf", "application/pdf")
    d2.download_button("⬇️ Excel", utils.receipt_excel(order, items), f"receipt_{oid}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
