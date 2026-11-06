"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).

All money is handled as integer cents and all percents as integer
millipercent (1 unit = 0.001%), as agreed in the pricing_api decision.
"""

import pricing

# Percent values are millipercent: 100% = 100000 units.
PERCENT_DENOMINATOR = 100000


def _round_half_up(numerator, denominator):
    """Integer division rounded half up (away from zero for negative values)."""
    sign = -1 if numerator < 0 else 1
    return sign * ((abs(numerator) + denominator // 2) // denominator)


def _percent_of(cents, millipct):
    """Return cents * millipct / 100000, rounded to the cent (half up)."""
    return _round_half_up(cents * millipct, PERCENT_DENOMINATOR)


def _format_money(cents):
    """Format integer cents as $X.YY, with a leading minus sign for negatives."""
    sign = "-" if cents < 0 else ""
    dollars, rest = divmod(abs(cents), 100)
    return f"{sign}${dollars}.{rest:02d}"


def _format_percent(millipct):
    """Format millipercent without trailing zeros: 10000 -> '10', 8250 -> '8.25'."""
    whole, frac = divmod(millipct, 1000)
    if frac == 0:
        return str(whole)
    return f"{whole}.{frac:03d}".rstrip("0")


def render_invoice(order):
    """Render an order as invoice text lines joined with newlines (no trailing newline)."""
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, with no discount and no tax.
        customer_name = customer_id
        discount_millipct = 0
        tax_millipct = 0
    else:
        customer_name = customer["name"]
        discount_millipct = customer["discount_millipct"]
        tax_millipct = customer["tax_millipct"]

    lines = [f"Customer: {customer_name}"]
    subtotal = 0
    for sku, quantity in order["lines"]:
        unit_price = pricing.unit_price_cents(sku)
        if unit_price is None:
            lines.append(f"UNKNOWN SKU: {sku}")
            continue
        amount = unit_price * quantity
        subtotal += amount
        lines.append(
            f"{sku} x{quantity} @ {_format_money(unit_price)} = {_format_money(amount)}"
        )

    discount = _percent_of(subtotal, discount_millipct)
    taxable = subtotal - discount
    tax = _percent_of(taxable, tax_millipct)
    total = taxable + tax

    lines.append(f"Subtotal: {_format_money(subtotal)}")
    lines.append(
        f"Discount ({_format_percent(discount_millipct)}%): -{_format_money(discount)}"
    )
    lines.append(f"Tax ({_format_percent(tax_millipct)}%): {_format_money(tax)}")
    lines.append(f"Total: {_format_money(total)}")
    return "\n".join(lines)
