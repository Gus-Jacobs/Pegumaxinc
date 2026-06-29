"""Session-based shopping cart helpers.

The cart lives in the Django session as a dict keyed by a stable line key:
    { "<merch_id>:<variant_id>": {
        merch_id, slug, name, variant_id, color, size,
        unit_price (str dollars), qty, image } }
"""
CART_SESSION_KEY = "academy_cart"
ACTIVE_PROMO_SESSION_KEY = "academy_active_promo"
# Which cart line the reward code's single-unit discount is applied to.
PROMO_TARGET_SESSION_KEY = "academy_promo_target"
# Per-line reward-code assignments: {line_key: code_string}. Each code may be
# assigned to at most one line (single-use, one unit each).
CART_CODES_SESSION_KEY = "academy_cart_codes"


def line_key(merch_id, variant_id) -> str:
    return f"{merch_id}:{variant_id or 0}"


def get_cart(session) -> dict:
    return session.get(CART_SESSION_KEY) or {}


def save_cart(session, cart) -> None:
    session[CART_SESSION_KEY] = cart
    session.modified = True


def clear_cart(session) -> None:
    if CART_SESSION_KEY in session:
        del session[CART_SESSION_KEY]
        session.modified = True


def _qty(line) -> int:
    try:
        return max(1, int(line.get("qty", 1)))
    except (TypeError, ValueError):
        return 1


def _price(line) -> float:
    try:
        return float(line.get("unit_price", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def cart_count(cart) -> int:
    return sum(_qty(li) for li in cart.values())


def cart_total(cart) -> float:
    return round(sum(_price(li) * _qty(li) for li in cart.values()), 2)


def cart_lines(cart):
    """Return display-ready line items with computed totals."""
    lines = []
    for key, li in cart.items():
        qty = _qty(li)
        unit = _price(li)
        lines.append({
            **li,
            "key": key,
            "qty": qty,
            "line_total": round(unit * qty, 2),
        })
    return lines
