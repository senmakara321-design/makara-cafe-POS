"""Stock control. Cashier: view + add/remove stock. Admin: also add/edit/delete products."""
import streamlit as st

import db
import utils

user = utils.require_login(["admin", "cashier"])
is_admin = user["role"] == "admin"
utils.title("boxes-stacked", "Stock Control")
utils.show_flash()

products = db.list_products()
labels = ["📦 Stock", "🔄 Add / Remove Stock", "📜 Stock Log"]
if is_admin:
    labels[1:1] = ["➕ Add Product", "✏️ Edit Product", "🖼️ Photos"]
tabs = dict(zip(labels, st.tabs(labels)))

# ---- overview ----
with tabs["📦 Stock"]:
    low = products[products["stock"] <= db.LOW_STOCK]
    if not low.empty:
        st.warning("⚠️ Low stock: " + ", ".join(f"{r['name']} ({r['stock']})" for _, r in low.iterrows()))
    show = products.drop(columns=["image"]).rename(columns={"id": "ID", "name": "Product", "price": "Price ($)", "stock": "Stock", "category": "Category", "description": "Description"})
    st.dataframe(show, hide_index=True, width="stretch")

# ---- add / remove stock (admin + cashier) ----
with tabs["🔄 Add / Remove Stock"]:
    if products.empty:
        st.info("No products yet.")
    else:
        opts = {int(r["id"]): f"{r['name']} (stock: {r['stock']})" for r in products.to_dict("records")}
        pid = st.selectbox("Product", list(opts), format_func=lambda k: opts[k], key="adj_pid")
        action = st.radio("Action", ["Add stock", "Remove stock"], horizontal=True)
        qty = st.number_input("Quantity", min_value=1, value=1, step=1)
        reason = st.text_input("Reason (optional)", placeholder="e.g. new delivery, damaged, expired")
        if st.button("Save", type="primary", key="adj_save"):
            try:
                db.adjust_stock(pid, qty if action == "Add stock" else -qty, reason, user["username"])
                utils.flash(f"{action}: {qty} × {opts[pid].split(' (')[0]}")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

# ---- admin only ----
if is_admin:
    with tabs["➕ Add Product"]:
        with st.form("new_product", clear_on_submit=True):
            name = st.text_input("Product name")
            c1, c2, c3 = st.columns(3)
            price = c1.number_input("Price ($)", min_value=0.0, value=1.0, step=0.25)
            stock = c2.number_input("Starting stock", min_value=0, value=0, step=1)
            category = c3.text_input("Category", value="Coffee")
            desc = st.text_input("Description (shown on the menu)")
            photo = st.file_uploader("Photo (optional)", type=["png", "jpg", "jpeg", "webp"])
            if st.form_submit_button("Add product"):
                if not name.strip():
                    st.error("Name is required")
                else:
                    try:
                        db.add_product(name, price, stock, category, user["username"],
                                       utils.save_product_image(photo) if photo else None, desc)
                        utils.flash(f"Added product: {name}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    with tabs["✏️ Edit Product"]:
        if products.empty:
            st.info("No products yet.")
        else:
            recs = {int(r["id"]): r for r in products.to_dict("records")}
            eid = st.selectbox("Product", list(recs), format_func=lambda k: recs[k]["name"], key="edit_pid")
            r = recs[eid]
            name = st.text_input("Name", r["name"], key=f"en_{eid}")
            c1, c2 = st.columns(2)
            price = c1.number_input("Price ($)", min_value=0.0, value=float(r["price"]), step=0.25, key=f"ep_{eid}")
            category = c2.text_input("Category", r["category"], key=f"ec_{eid}")
            desc = st.text_input("Description", r.get("description") or "", key=f"ed_{eid}")
            cur_photo = utils.product_image(utils.photo_for(r))
            p1, p2 = st.columns([1, 2])
            if cur_photo:
                p1.image(str(cur_photo), caption="Current photo")
            new_photo = p2.file_uploader("New photo (optional)", type=["png", "jpg", "jpeg", "webp"], key=f"ephoto_{eid}")
            remove_photo = p2.checkbox("Remove photo", key=f"erm_{eid}") if cur_photo else False
            b1, b2, _ = st.columns([1, 1, 3])
            if b1.button("Save changes", type="primary"):
                try:
                    img = utils.save_product_image(new_photo) if new_photo else ("" if remove_photo else None)
                    db.update_product(eid, name, price, category, img, desc)
                    utils.flash("Product updated")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
            if b2.button("🗑️ Delete"):
                db.delete_product(eid)
                utils.flash(f"Deleted {r['name']} (old orders are kept)")
                st.rerun()

if is_admin:
    with tabs["🖼️ Photos"]:
        st.write("Upload **real photos** for many products at once. Name each file like the product "
                 "(e.g. `Iced Coffee.jpg`, `latte.png`) and it is matched automatically.")
        files = st.file_uploader("Photos", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="bulk_photos")
        if files and st.button("Save photos", type="primary", key="bulk_save"):
            ok, bad = utils.assign_photos(files)
            msg = f"Saved {len(ok)} photo(s)." + ("  \n" + "  \n".join(ok) if ok else "")
            if bad:
                msg += "  \nNo product found for: " + ", ".join(bad)
            utils.flash(msg)
            st.rerun()
        st.divider()
        st.write("Or paste a **direct image link** (right-click a picture → *Copy image address*):")
        recs_p = {int(r["id"]): r for r in products.to_dict("records")}
        lc1, lc2 = st.columns([1, 2])
        pid_l = lc1.selectbox("Product", list(recs_p), format_func=lambda k: recs_p[k]["name"], key="link_pid")
        url_l = lc2.text_input("Image link", placeholder="https://.../photo.jpg", key="link_url")
        if st.button("Download & save", key="link_save"):
            try:
                p = recs_p[pid_l]
                db.update_product(pid_l, p["name"], p["price"], p["category"], utils.save_image_from_url(url_l))
                utils.flash(f"Photo saved for {p['name']}")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
        st.caption("Only use pictures you own or that are free to use commercially (e.g. your own photos, Unsplash, Pexels).")
        have = [r["name"] for r in products.to_dict("records") if utils.photo_for(r)]
        missing = [r["name"] for r in products.to_dict("records") if not utils.photo_for(r)]
        st.caption(f"With photo: {len(have)} • Still using a drawing: {len(missing)}" + (f" ({', '.join(missing)})" if missing else ""))

with tabs["📜 Stock Log"]:
    st.dataframe(db.stock_log(), hide_index=True, width="stretch")
