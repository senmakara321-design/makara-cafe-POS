"""Admin only: sales report per day / month, product sales in $ or quantity, export PDF + Excel."""
from datetime import date, timedelta

import streamlit as st

import db
import utils

user = utils.require_login(["admin"])
utils.title("chart-line", "Sales Reports")

c1, c2, c3, c4 = st.columns(4)
start = c1.date_input("From", date.today() - timedelta(days=29))
end = c2.date_input("To", date.today())
period_label = c3.radio("Group by", ["Day", "Month"], horizontal=True)
metric_label = c4.radio("Show product sales as", ["Revenue ($)", "Quantity (stock sold)"])
period = period_label.lower()
metric = "Revenue" if metric_label.startswith("Revenue") else "Qty_Sold"

sales = db.sales_by_period(period, start, end)
by_product = db.product_sales(start, end)
by_pp = db.product_sales_by_period(period, start, end)

if sales.empty:
    st.info("No sales in this period.")
    if st.button("Load demo sales data (30 days)"):
        db.seed_demo_sales()
        st.rerun()
    st.stop()

m1, m2, m3 = st.columns(3)
m1.metric("Revenue", f"${sales['Revenue'].sum():,.2f}")
m2.metric("Orders", int(sales["Orders"].sum()))
m3.metric("Items sold", int(by_product["Qty_Sold"].sum()))

st.subheader(f"Revenue per {period}")
st.bar_chart(sales.set_index("Period")["Revenue"])
st.dataframe(sales, hide_index=True, width="stretch")

st.subheader(f"Product sales ({metric_label})")
st.bar_chart(by_product.set_index("Product")[metric])
st.dataframe(by_product, hide_index=True, width="stretch")

st.subheader(f"Each product per {period} ({metric_label})")
pivot = by_pp.pivot_table(index="Period", columns="Product", values=metric, aggfunc="sum", fill_value=0).reset_index()
st.dataframe(pivot, hide_index=True, width="stretch")

st.subheader("⬇️ Export")
subtitle = f"{start} to {end} (grouped by {period})"
e1, e2 = st.columns(2)
e1.download_button(
    "Download PDF",
    utils.report_pdf("Sales Report", subtitle, [("Sales", sales), ("Product sales", by_product)]),
    f"sales_report_{start}_{end}.pdf", "application/pdf",
)
e2.download_button(
    "Download Excel",
    utils.report_excel({"Sales": sales, "By Product": by_product, "Product by Period": pivot}),
    f"sales_report_{start}_{end}.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

with st.expander("Demo data"):
    if st.button("Add 30 days of demo sales"):
        db.seed_demo_sales(seed=date.today().toordinal())
        st.rerun()
