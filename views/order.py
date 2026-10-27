"""Order page: menu (left) + Bills / payment panel (right).
Used by Admin and Cashier."""
import time
from html import escape

import streamlit as st

import db
import drinks
import khqr
import utils

user = utils.require_login(["admin", "cashier"])

st.session_state.setdefault("cart", {})  # {product_id: qty}
cart = st.session_state["cart"]

CAT_ICON = {"All": ":material/apps:", "Coffee": ":material/coffee:", "Tea": ":material/emoji_food_beverage:",
            "Smoothie": ":material/blender:", "Bakery": ":material/bakery_dining:", "Other": ":material/local_drink:"}
FA_ICON = {"Coffee": ("mug-hot", "#6F4E37"), "Tea": ("leaf", "#4F7942"), "Smoothie": ("blender", "#E8743B"),
           "Bakery": ("bread-slice", "#C98B3C"), "Other": ("bottle-water", "#4A90A4")}
PAY_ICON = {"Cash": ":material/payments:", "KHQR": ":material/qr_code_2:", "Photo QR (demo)": ":material/image:"}


def reset_cart():
    st.session_state["cart"] = {}
    for k in [k for k in st.session_state if k.startswith("qty_")]:
        del st.session_state[k]


def pic(r):
    """Picture for a product: uploaded photo > drawing from drinks.py > icon."""
    img = utils.photo_for(r)
    if img:
        return f'<div class="mk-pic"><img src="/app/static/products/{escape(img)}"></div>'
    art = drinks.pick(r["name"], r["category"])
    if art:
        return f'<div class="mk-pic mk-tile--{drinks.TILE[art]}">{drinks.SVGS[art]}</div>'
    ic, col = FA_ICON.get(r["category"], ("mug-saucer", "#6F4E37"))
    return f'<div class="mk-pic mk-tile--plain">{utils.fa(ic, 30, col)}</div>'


# ---------- after an order is saved: receipt / pending message ----------
last = st.session_state.get("last_order")
if last:
    order = db.get_order(last)
    items = db.get_order_items(last)
    utils.html('<h1 class="mk-h1">Thank you!</h1>')
    if order["status"] == "Paid":
        st.success(f"Payment successful - Order #{last}")
        st.dataframe(items, hide_index=True)
        st.write(f"**Total: ${order['total']:.2f}** • {order['payment_method']} • {order['date']}")
        d1, d2, _ = st.columns([1, 1, 3])
        d1.download_button("Receipt PDF", utils.receipt_pdf(order, items), f"receipt_{last}.pdf", "application/pdf",
                           icon=":material/picture_as_pdf:")
        d2.download_button("Receipt Excel", utils.receipt_excel(order, items), f"receipt_{last}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/table_view:")
    else:
        st.success(f"Order #{last} created.")
        st.dataframe(items, hide_index=True)
    if st.button("New order", type="primary", icon=":material/add:"):
        del st.session_state["last_order"]
        st.rerun()
    st.stop()

products = db.list_products()
by_id = {int(r["id"]): r for r in products.to_dict("records")}
for pid in list(cart):
    if pid not in by_id:
        del cart[pid]

left, right = st.columns([5, 2.4], gap="large")

# =====================================================  LEFT: menu
with left:
    t1, t2 = st.columns([3, 2])
    with t1:
        utils.html('<h1 class="mk-h1">Choose Category</h1>')
    with t2:
        q = st.text_input("Search", placeholder="Search menu...", label_visibility="collapsed", key="menu_search")

    cats = ["All"] + sorted(products["category"].unique().tolist())
    with st.container(key="cats"):
        cat = st.pills("Category", cats, default="All", selection_mode="single", label_visibility="collapsed",
                       format_func=lambda c: f"{CAT_ICON.get(c, ':material/restaurant:')} {c}", key="cat_pick") or "All"

    shown = products if cat == "All" else products[products["category"] == cat]
    if q.strip():
        k = q.strip().lower()
        shown = shown[shown["name"].str.lower().str.contains(k, regex=False) |
                      shown["description"].fillna("").str.lower().str.contains(k, regex=False)]
    utils.html(f'<div class="mk-row"><h2 class="mk-h2">{escape(cat)} Menu</h2>'
               f'<span class="mk-muted">{len(shown)} Result{"s" if len(shown) != 1 else ""}</span></div>')

    if shown.empty:
        st.info("No items found.")
    cols = st.columns(2, gap="medium")
    for i, r in enumerate(shown.to_dict("records")):
        out = r["stock"] <= 0
        with cols[i % 2].container(key=f"card_{r['id']}"):
            desc = escape(r.get("description") or "")
            stock = f'<div class="mk-stock">Stock: {r["stock"]}</div>'
            utils.html(f'<div class="mk-item">{pic(r)}<div class="mk-info">'
                       f'<div class="mk-name">{escape(r["name"])}</div><div class="mk-desc">{desc}</div>'
                       f'<div class="mk-price"><sup>&#36;</sup>{r["price"]:.2f}</div>{stock}</div></div>')
            if st.button("Out of stock" if out else "Add to Billing", key=f"add_{r['id']}", type="primary", disabled=out):
                pid = int(r["id"])
                cart[pid] = min(cart.get(pid, 0) + 1, int(r["stock"]))
                st.session_state[f"qty_{pid}"] = cart[pid]
                st.rerun()

# =====================================================  RIGHT: profile + bills + payment
with right:
    utils.html('<span id="cart-anchor"></span>')
    role_txt = "an Admin" if user["role"] == "admin" else "a Cashier"
    utils.html(f'<div class="mk-profile"><div class="mk-avatar">{escape(user["username"][0].upper())}</div>'
               f'<div><div class="mk-muted">I\'m {role_txt}</div><div class="mk-uname">{escape(user["username"])}</div></div></div>')

    with st.container(key="bills"):
        utils.html('<h2 class="mk-h2">Bills</h2>')
        if not cart:
            utils.html('<div class="mk-empty">Your bill is empty.<br>Tap <b>Add to Billing</b> on a menu item.</div>')
        total = 0.0
        for pid in list(cart):
            p = by_id[pid]
            mx = max(int(p["stock"]), 1)
            st.session_state.setdefault(f"qty_{pid}", cart[pid])
            st.session_state[f"qty_{pid}"] = min(st.session_state[f"qty_{pid}"], mx)
            c1, c2, c3 = st.columns([5, 3.2, 1], vertical_alignment="center")
            qty_now = st.session_state[f"qty_{pid}"]
            with c1:
                utils.html(f'<div class="mk-bill">{pic(p)}<div><div class="mk-bname">{escape(p["name"])}</div>'
                           f'<div class="mk-bprice">&#36;{p["price"] * qty_now:.2f}</div></div></div>')
            qty = c2.number_input("qty", min_value=1, max_value=mx, key=f"qty_{pid}", label_visibility="collapsed")
            cart[pid] = int(qty)
            if c3.button("", key=f"rm_{pid}", icon=":material/close:", type="tertiary"):
                del cart[pid]
                st.session_state.pop(f"qty_{pid}", None)
                st.rerun()
            total += p["price"] * qty

        utils.html(f'<div class="mk-sum"><span>Subtotal</span><span>&#36;{total:,.2f}</span></div>'
                   f'<div class="mk-total"><span>Total</span><span>&#36;{total:,.2f}</span></div>')

        if cart:
            utils.html('<h3 class="mk-h3">Payment Method</h3>')
            methods = ["Cash", "KHQR", "Photo QR (demo)"]
            with st.container(key="pay"):
                method = st.pills("Method", methods, default=methods[0], selection_mode="single",
                                  label_visibility="collapsed", format_func=lambda m: f"{PAY_ICON[m]} {m}",
                                  key="pay_pick") or methods[0]
            ok_to_pay = True

            if method == "Cash":
                received = st.number_input("Cash received ($)", min_value=0.0, value=float(round(total, 2)), step=0.5)
                if received < total:
                    st.error("Not enough cash")
                    ok_to_pay = False
                else:
                    st.info(f"Change: ${received - total:,.2f}")

            elif method == "KHQR":
                bakong_id = db.get_setting("bakong_id", db.DEFAULT_BAKONG_ID)
                cache = st.session_state.get("khqr_cache")
                if not cache or cache["total"] != round(total, 2) or time.time() > cache["expires"]:
                    payload = khqr.build_khqr(bakong_id, db.get_setting("merchant_name", "Makara Cafe"),
                                              db.get_setting("merchant_city", "Phnom Penh"), round(total, 2),
                                              bill_number=f"T{int(time.time())}")
                    cache = {"total": round(total, 2), "payload": payload, "expires": time.time() + 540}
                    st.session_state["khqr_cache"] = cache
                st.image(utils.qr_png(cache["payload"]), caption=f"KHQR - scan to pay ${total:,.2f}", width=170)
                st.caption("Demo KHQR (set the real Bakong ID in Users & KHQR). Press Confirm after the bank app shows success."
                           if bakong_id == db.DEFAULT_BAKONG_ID else "Press Confirm after the bank app shows success.")

            elif method == "Photo QR (demo)":
                qr = utils.find_qr_image()
                if qr:
                    st.image(str(qr), caption=f"Scan to pay ${total:,.2f}  (DEMO QR)", width=170)
                else:
                    st.warning("Put your QR photo inside the **Photo/** folder (e.g. Photo/qr.png).")

            if st.button("Confirm Payment", type="primary", disabled=not ok_to_pay, key="confirm_btn",
                         icon=":material/check_circle:"):
                try:
                    oid = db.create_order(
                        dict(cart), user["username"], method.replace(" (demo)", ""), status="Paid")
                    reset_cart()
                    st.session_state.pop("khqr_cache", None)
                    st.session_state["last_order"] = oid
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
            if st.button("Clear bill", key="clear_btn", type="tertiary", icon=":material/delete:"):
                reset_cart()
                st.rerun()
