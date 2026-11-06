"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing


def _money(cents):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(text):
    # Plain decimal string ("8.25", "10", "0") -> no trailing zeros for display.
    value = Decimal(text).normalize()
    return format(value, "f")


def _round_cents(value):
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _apply_percent(cents, percent_text):
    # cents * percent / 100, rounded half up to the cent.
    return _round_cents(Decimal(cents) * Decimal(percent_text) / Decimal(100))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        name = customer_id
        discount_percent = "0"
        tax_percent = "0"
    else:
        name = customer["name"]
        discount_percent = customer["discount_percent"]
        tax_percent = customer["tax_percent"]

    lines = [f"Customer: {name}"]
    subtotal = 0
    for sku, quantity in order["lines"]:
        unit_price = pricing.get_item_price(sku)
        if unit_price is None:
            lines.append(f"UNKNOWN SKU: {sku}")
            continue
        amount = unit_price * quantity
        subtotal += amount
        lines.append(f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}")

    discount = _apply_percent(subtotal, discount_percent)
    taxable = subtotal - discount
    tax = _apply_percent(taxable, tax_percent)
    total = taxable + tax

    lines.append(f"Subtotal: {_money(subtotal)}")
    lines.append(f"Discount ({_percent(discount_percent)}%): -{_money(discount)}")
    lines.append(f"Tax ({_percent(tax_percent)}%): {_money(tax)}")
    lines.append(f"Total: {_money(total)}")
    return "\n".join(lines)
