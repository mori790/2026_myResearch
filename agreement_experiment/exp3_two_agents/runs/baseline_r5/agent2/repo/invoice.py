"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing


def _money(cents):
    return f"${cents // 100}.{cents % 100:02d}"


def _percent(pct):
    return format(Decimal(pct).normalize(), "f")


def _round_cents(value):
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        name = customer_id
        discount_pct = Decimal("0")
        tax_pct = Decimal("0")
    else:
        name = customer["name"]
        discount_pct = customer["discount_pct"]
        tax_pct = customer["tax_pct"]

    lines = [f"Customer: {name}"]
    subtotal = 0
    for sku, qty in order["lines"]:
        unit_price = pricing.get_unit_price_cents(sku)
        if unit_price is None:
            lines.append(f"UNKNOWN SKU: {sku}")
            continue
        amount = unit_price * qty
        subtotal += amount
        lines.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}")

    discount = _round_cents(Decimal(subtotal) * discount_pct / 100)
    taxable = subtotal - discount
    tax = _round_cents(Decimal(taxable) * tax_pct / 100)
    total = taxable + tax

    lines.append(f"Subtotal: {_money(subtotal)}")
    lines.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    lines.append(f"Tax ({_percent(tax_pct)}%): {_money(tax)}")
    lines.append(f"Total: {_money(total)}")
    return "\n".join(lines)
