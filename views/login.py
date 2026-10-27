"""Staff login for Makara Café POS (Admin and Cashier only)."""
import streamlit as st
import db
import utils

utils.title("mug-hot", "Makařa Café")
_, mid, _ = st.columns([1, 1.2, 1])
with mid:
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        ok = st.form_submit_button("Login")
    if ok:
        user = db.login(u.strip(), p)
        if user and user["role"] in ("admin", "cashier"):
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("ឈ្មោះអ្នកប្រើប្រាស់ លេខសម្ងាត់ ឬតួនាទីបុគ្គលិកមិនត្រឹមត្រូវ។")
    st.info("គណនីសម្រាប់សាកល្បង → admin / admin123 • cashier / cashier123")
    st.caption("គណនីបុគ្គលិកត្រូវបានបង្កើត និងគ្រប់គ្រងដោយអ្នកគ្រប់គ្រង។")
