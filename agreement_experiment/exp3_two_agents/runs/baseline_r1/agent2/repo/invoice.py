"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing

CENT = Decimal("0.01")


def _money(amount):
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _percent_text(percent):
    # Show percents without trailing zeros, e.g. "10", "8.25", "0".
    return format(percent.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        name = customer_id
        discount_percent = Decimal("0")
        tax_percent = Decimal("0")
    else:
        name = customer["name"]
        discount_percent = Decimal(customer["discount_percent"])
        tax_percent = Decimal(customer["tax_percent"])

    lines = [f"Customer: {name}"]
    subtotal = Decimal("0")
    for sku, quantity in order["lines"]:
        unit_cents = pricing.get_unit_price_cents(sku)
        if unit_cents is None:
            lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = Decimal(unit_cents) / 100
        amount = _money(unit_price * quantity)
        subtotal += amount
        lines.append(f"{sku} x{quantity} @ ${_money(unit_price):.2f} = ${amount:.2f}")

    discount = _money(subtotal * discount_percent / 100)
    taxable = subtotal - discount
    tax = _money(taxable * tax_percent / 100)
    total = taxable + tax

    lines.append(f"Subtotal: ${subtotal:.2f}")
    lines.append(f"Discount ({_percent_text(discount_percent)}%): -${discount:.2f}")
    lines.append(f"Tax ({_percent_text(tax_percent)}%): ${tax:.2f}")
    lines.append(f"Total: ${total:.2f}")
    return "\n".join(lines)
