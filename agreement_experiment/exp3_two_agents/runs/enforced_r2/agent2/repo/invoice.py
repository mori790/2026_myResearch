"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing


def _money(cents):
    """Format an integer amount of cents as dollars, e.g. 2500 -> '$25.00'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(text):
    """Format a decimal-string percent without trailing zeros, e.g. '10.0' -> '10'."""
    return format(Decimal(text).normalize(), "f")


def _round_cents(value):
    """Round a Decimal number of cents to a whole cent, half up."""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: show the id, with no discount and no tax.
        name = customer_id
        discount_percent = "0"
        tax_percent = "0"
    else:
        name = customer["name"]
        discount_percent = customer["discount_percent"]
        tax_percent = customer["tax_percent"]

    lines = [f"Customer: {name}"]
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        unit_cents = pricing.unit_price_cents(sku)
        if unit_cents is None:
            lines.append(f"UNKNOWN SKU: {sku}")
            continue
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        lines.append(
            f"{sku} x{quantity} @ {_money(unit_cents)} = {_money(amount_cents)}"
        )

    discount_cents = _round_cents(
        Decimal(subtotal_cents) * Decimal(discount_percent) / Decimal(100)
    )
    taxable_cents = subtotal_cents - discount_cents
    tax_cents = _round_cents(
        Decimal(taxable_cents) * Decimal(tax_percent) / Decimal(100)
    )
    total_cents = taxable_cents + tax_cents

    lines.append(f"Subtotal: {_money(subtotal_cents)}")
    lines.append(
        f"Discount ({_percent(discount_percent)}%): -{_money(discount_cents)}"
    )
    lines.append(f"Tax ({_percent(tax_percent)}%): {_money(tax_cents)}")
    lines.append(f"Total: {_money(total_cents)}")

    return "\n".join(lines)
