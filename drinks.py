"""Flat illustrations (inline SVG) for the menu cards - no internet, no image files needed.
Used when a product has no uploaded photo. Add or edit drawings here."""

W = 'viewBox="0 0 240 180" xmlns="http://www.w3.org/2000/svg"'


def _hot_cup(liquid="#6F4E37", art="", extra=""):
    return f'''<svg {W}>
<path d="M98 50c-8-10 8-16 0-28M122 50c-8-10 8-16 0-28M146 50c-8-10 8-16 0-28" stroke="#fff" stroke-opacity=".75" stroke-width="5" fill="none" stroke-linecap="round"/>
<ellipse cx="122" cy="152" rx="80" ry="12" fill="#fff" opacity=".95"/>
<path d="M74 72h96v36a48 40 0 0 1-96 0z" fill="#fff"/>
<path d="M170 84h10a16 16 0 0 1 0 32h-14" fill="none" stroke="#fff" stroke-width="9"/>
<ellipse cx="122" cy="72" rx="48" ry="9" fill="{liquid}"/>{art}{extra}
</svg>'''


def _glass(liquid, extras="", straw="#D9534F"):
    return f'''<svg {W}>
<rect x="128" y="14" width="8" height="74" rx="4" fill="{straw}" transform="rotate(12 132 51)"/>
<path d="M82 40h76l-9 112a8 8 0 0 1-8 7H99a8 8 0 0 1-8-7z" fill="#fff" fill-opacity=".55" stroke="#fff" stroke-width="4"/>
<path d="M87 78h66l-6 74a6 6 0 0 1-6 5h-42a6 6 0 0 1-6-5z" fill="{liquid}"/>{extras}
</svg>'''


ICE = '''<rect x="98" y="84" width="22" height="22" rx="4" fill="#fff" opacity=".6" transform="rotate(-10 109 95)"/>
<rect x="124" y="102" width="20" height="20" rx="4" fill="#fff" opacity=".5" transform="rotate(14 134 112)"/>
<rect x="100" y="120" width="18" height="18" rx="4" fill="#fff" opacity=".45" transform="rotate(-6 109 129)"/>'''


def _cake(layer, filling, top, decor):
    return f'''<svg {W}>
<ellipse cx="120" cy="152" rx="84" ry="12" fill="#fff" opacity=".95"/>
<rect x="62" y="96" width="116" height="42" rx="4" fill="{filling}"/>
<rect x="62" y="124" width="116" height="14" rx="4" fill="{layer}"/>
<rect x="62" y="96" width="116" height="10" fill="{layer}"/>
<path d="M62 96q0-14 14-14h88q14 0 14 14z" fill="{top}"/>{decor}
</svg>'''


SVGS = {
    "hot_coffee": _hot_cup(),
    "latte": _hot_cup("#C8A27A", '<path d="M122 78c-5-7-17-2-12 5l12 9 12-9c5-7-7-12-12-5z" fill="#F3E5D0"/>'),
    "tea": _hot_cup("#9BC15E", '', '<path d="M140 72c4-16 12-24 20-28" stroke="#fff" stroke-width="3" fill="none"/><rect x="156" y="36" width="18" height="13" rx="2" fill="#fff"/><path d="M186 30c22 0 32 14 32 30-20 0-32-12-32-30z" fill="#5C8A3A"/>'),
    "iced_coffee": _glass("#6F4E37", ICE),
    "boba": _glass("#C9A27A", '<g fill="#3B2A20"><circle cx="106" cy="146" r="6"/><circle cx="122" cy="148" r="6"/><circle cx="138" cy="146" r="6"/><circle cx="114" cy="134" r="6"/><circle cx="130" cy="134" r="6"/></g>', "#F2A7B8"),
    "smoothie_mango": _glass("#F6B83C", '<circle cx="158" cy="44" r="14" fill="#F08A24"/><path d="M104 96q16-10 34 0" stroke="#fff" stroke-opacity=".5" stroke-width="5" fill="none" stroke-linecap="round"/>', "#4CAF50"),
    "smoothie_berry": _glass("#E8576E", '<circle cx="158" cy="44" r="14" fill="#C62E4A"/><path d="M104 96q16-10 34 0" stroke="#fff" stroke-opacity=".5" stroke-width="5" fill="none" stroke-linecap="round"/>', "#fff"),
    "smoothie": _glass("#8BC34A", '<path d="M104 96q16-10 34 0" stroke="#fff" stroke-opacity=".5" stroke-width="5" fill="none" stroke-linecap="round"/>', "#fff"),
    "croissant": f'''<svg {W}><g transform="translate(120 96)">
<ellipse cx="-50" cy="16" rx="28" ry="20" transform="rotate(35 -50 16)" fill="#D58E3A"/>
<ellipse cx="50" cy="16" rx="28" ry="20" transform="rotate(-35 50 16)" fill="#D58E3A"/>
<ellipse cx="-74" cy="38" rx="16" ry="12" transform="rotate(50 -74 38)" fill="#C77D2E"/>
<ellipse cx="74" cy="38" rx="16" ry="12" transform="rotate(-50 74 38)" fill="#C77D2E"/>
<ellipse cx="0" cy="0" rx="40" ry="32" fill="#E3A24F"/>
<path d="M-22-26c7 14 7 38 0 52M4-30c7 16 7 42 0 60M28-24c6 12 6 34 0 48" stroke="#B9702A" stroke-width="4" fill="none" stroke-linecap="round" opacity=".7"/>
</g></svg>''',
    "cake_choc": _cake("#6B4330", "#F3E5D0", "#3E2418", '<circle cx="120" cy="76" r="9" fill="#D9344F"/><path d="M120 68c2-6 6-9 10-10" stroke="#3E7D32" stroke-width="3" fill="none"/>'),
    "cheesecake": _cake("#C98B3C", "#FBEBC0", "#E4586E", '<circle cx="104" cy="82" r="7" fill="#C62E4A"/><circle cx="130" cy="80" r="7" fill="#C62E4A"/>'),
    "water": f'''<svg {W}>
<rect x="108" y="20" width="24" height="14" rx="3" fill="#2F80ED"/>
<path d="M108 34h24v14c0 8 24 14 24 38v58a12 12 0 0 1-12 12H96a12 12 0 0 1-12-12V86c0-24 24-30 24-38z" fill="#fff" fill-opacity=".6" stroke="#fff" stroke-width="4"/>
<rect x="88" y="116" width="64" height="34" rx="6" fill="#5BB7F0" opacity=".85"/>
<rect x="85" y="88" width="70" height="24" fill="#2F80ED" opacity=".9"/>
</svg>''',
}

# tile colour class (see style.css) for each drawing
TILE = {"hot_coffee": "coffee", "latte": "coffee", "iced_coffee": "coffee", "boba": "tea", "tea": "tea",
        "smoothie_mango": "mango", "smoothie_berry": "berry", "smoothie": "tea",
        "croissant": "bakery", "cake_choc": "bakery", "cheesecake": "bakery", "water": "water"}


def pick(name, category=""):
    """Choose a drawing from the product name (then the category)."""
    n = (name or "").lower()
    rules = [("iced", "iced_coffee"), ("latte", "latte"), ("cappuccino", "latte"), ("milk tea", "boba"),
             ("bubble", "boba"), ("boba", "boba"), ("tea", "tea"), ("mango", "smoothie_mango"),
             ("strawberry", "smoothie_berry"), ("berry", "smoothie_berry"), ("smoothie", "smoothie"),
             ("croissant", "croissant"), ("chocolate", "cake_choc"), ("cheesecake", "cheesecake"),
             ("cake", "cheesecake"), ("water", "water"), ("coffee", "hot_coffee")]
    for key, art in rules:
        if key in n:
            return art
    return {"Coffee": "hot_coffee", "Tea": "tea", "Smoothie": "smoothie", "Bakery": "croissant"}.get(category)


def tile_html(name, category=""):
    """HTML for a menu-card picture, or None if there is no drawing for this product."""
    art = pick(name, category)
    if not art:
        return None
    return f'<div class="mk-tile mk-tile--{TILE[art]}">{SVGS[art]}</div>'
