"""Admin: manage users + KHQR settings."""
import streamlit as st

import db
import khqr
import utils

user = utils.require_login(["admin"])
utils.title("gear", "Users & KHQR")
utils.show_flash()
tab_u, tab_k = st.tabs(["👥 Users", "💳 KHQR settings"])

with tab_u:
    users = db.list_users()
    st.dataframe(users.rename(columns={"id": "ID", "username": "Username", "role": "Role"}), hide_index=True, width="stretch")

    st.subheader("Create user")
    with st.form("new_user", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        nu = c1.text_input("Username")
        npw = c2.text_input("Password", type="password")
        nr = c3.selectbox("Role", list(db.ROLES), index=1)
        if st.form_submit_button("Create"):
            try:
                db.create_user(nu, npw, nr)
                utils.flash(f"Created {nr} '{nu}'")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    st.subheader("Change password / delete")
    recs = {int(r["id"]): r for r in users.to_dict("records")}
    uid = st.selectbox("User", list(recs), format_func=lambda k: f"{recs[k]['username']} ({recs[k]['role']})")
    c1, c2 = st.columns(2)
    with c1:
        pw = st.text_input("New password", type="password", key="chg_pw")
        if st.button("Change password"):
            try:
                db.set_password(uid, pw)
                utils.flash("Password changed")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    with c2:
        st.write("")
        st.write("")
        if st.button("🗑️ Delete user"):
            try:
                db.delete_user(uid, user["username"])
                utils.flash("User deleted")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

with tab_k:
    st.write("These details go inside every KHQR code the shop shows to pay.")
    bid = st.text_input("Bakong account ID", db.get_setting("bakong_id", db.DEFAULT_BAKONG_ID),
                        help="Example: yourname@aba - copy it from your bank's KHQR / Bakong profile")
    name = st.text_input("Merchant name (max 25, English)", db.get_setting("merchant_name", "Makara Cafe"))
    city = st.text_input("City", db.get_setting("merchant_city", "Phnom Penh"))
    if st.button("Save KHQR settings", type="primary"):
        db.set_setting("bakong_id", bid.strip())
        db.set_setting("merchant_name", name.strip()[:25])
        db.set_setting("merchant_city", city.strip()[:15])
        utils.flash("KHQR settings saved")
        st.rerun()
    st.subheader("Preview ($1.00)")
    payload = khqr.build_khqr(bid.strip() or db.DEFAULT_BAKONG_ID, name.strip() or "Makara Cafe", city.strip() or "Phnom Penh", 1.00)
    st.image(utils.qr_png(payload), width=240)
    with st.expander("KHQR text inside the QR"):
        st.code(payload)
    st.caption("This app does not check with the bank whether money arrived - the cashier presses Confirm after seeing the success screen.")
