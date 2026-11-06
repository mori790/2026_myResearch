"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).
"""

from decimal import ROUND_HALF_UP, Decimal

import pricing


def _money(cents):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(value):
    # Drop trailing zeros: Decimal("10.00") -> "10", Decimal("8.250") -> "8.25".
    text = format(value.normalize(), "f")
    return text


def _percent_of(cents, percent):
    # cents * percent / 100, rounded half up to the nearest cent.
    amount = Decimal(cents) * percent / Decimal(100)
    return int(amount.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        name = customer_id
        discount_percent = Decimal(0)
        tax_percent = Decimal(0)
    else:
        name = customer["name"]
        discount_percent = customer["discount_percent"]
        tax_percent = customer["tax_percent"]

    lines = [f"Customer: {name}"]
    subtotal = 0
    for sku, quantity in order["lines"]:
        unit_cents = pricing.get_unit_price_cents(sku)
        if unit_cents is None:
            lines.append(f"UNKNOWN SKU: {sku}")
            continue
        amount = unit_cents * quantity
        subtotal += amount
        lines.append(f"{sku} x{quantity} @ {_money(unit_cents)} = {_money(amount)}")

    discount = _percent_of(subtotal, discount_percent)
    taxable = subtotal - discount
    tax = _percent_of(taxable, tax_percent)
    total = taxable + tax

    lines.append(f"Subtotal: {_money(subtotal)}")
    lines.append(f"Discount ({_percent(discount_percent)}%): -{_money(discount)}")
    lines.append(f"Tax ({_percent(tax_percent)}%): {_money(tax)}")
    lines.append(f"Total: {_money(total)}")
    return "\n".join(lines)
