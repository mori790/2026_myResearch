"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).

Money is handled as integer cents. Percentages are Decimal values in percent
units (10 means 10%), as agreed in the pricing-api decision.
"""

from decimal import ROUND_HALF_UP, Decimal

import pricing


def _round_cents(amount):
    """Round a Decimal amount in cents to a whole cent, half up."""
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _format_money(cents):
    """Format integer cents as dollars: 2500 -> $25.00, -250 -> -$2.50."""
    sign = "-" if cents < 0 else ""
    dollars, rest = divmod(abs(cents), 100)
    return f"{sign}${dollars}.{rest:02d}"


def _format_percent(pct):
    """Format a Decimal percent without trailing zeros: 10 -> 10, 8.250 -> 8.25."""
    text = format(pct, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def render_invoice(order):
    """Return the invoice for order as text, with no trailing newline."""
    customer_id = order["customer"]
    try:
        customer = pricing.get_customer(customer_id)
    except KeyError:
        name = customer_id
        discount_pct = Decimal("0")
        tax_pct = Decimal("0")
    else:
        name = customer["name"]
        discount_pct = Decimal(str(customer["discount_pct"]))
        tax_pct = Decimal(str(pricing.get_tax_pct(customer["region"])))

    lines = [f"Customer: {name}"]
    subtotal = 0
    for sku, qty in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = item["price_cents"]
        amount = unit_cents * qty
        subtotal += amount
        lines.append(
            f"{sku} x{qty} @ {_format_money(unit_cents)} = {_format_money(amount)}"
        )

    discount = _round_cents(Decimal(subtotal) * discount_pct / 100)
    tax = _round_cents(Decimal(subtotal - discount) * tax_pct / 100)
    total = subtotal - discount + tax

    lines.append(f"Subtotal: {_format_money(subtotal)}")
    lines.append(
        f"Discount ({_format_percent(discount_pct)}%): -{_format_money(discount)}"
    )
    lines.append(f"Tax ({_format_percent(tax_pct)}%): {_format_money(tax)}")
    lines.append(f"Total: {_format_money(total)}")
    return "\n".join(lines)
