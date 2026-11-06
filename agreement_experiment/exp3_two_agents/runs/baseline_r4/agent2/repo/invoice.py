"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing


def _money(cents):
    """Format integer cents as dollars, e.g. 2500 -> '$25.00', -250 -> '-$2.50'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s$%d.%02d" % (sign, cents // 100, cents % 100)


def _percent(value):
    """Format a percent without trailing zeros, e.g. Decimal('10') -> '10', Decimal('8.250') -> '8.25'."""
    return format(Decimal(str(value)).normalize(), "f")


def _round_cents(value):
    """Round a Decimal amount of cents to a whole number of cents, half up."""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, with no discount and no tax.
        name = customer_id
        discount_pct = Decimal("0")
        tax_pct = Decimal("0")
    else:
        name = customer["name"]
        discount_pct = Decimal(str(customer["discount_percent"]))
        tax_pct = Decimal(str(customer["tax_percent"]))

    lines = ["Customer: %s" % name]
    subtotal = 0
    for sku, quantity in order["lines"]:
        unit_price = pricing.get_unit_price_cents(sku)
        if unit_price is None:
            lines.append("UNKNOWN SKU: %s" % sku)
            continue
        amount = unit_price * quantity
        subtotal += amount
        lines.append("%s x%d @ %s = %s" % (sku, quantity, _money(unit_price), _money(amount)))

    discount = _round_cents(Decimal(subtotal) * discount_pct / Decimal(100))
    taxable = subtotal - discount
    tax = _round_cents(Decimal(taxable) * tax_pct / Decimal(100))
    total = subtotal - discount + tax

    lines.append("Subtotal: %s" % _money(subtotal))
    lines.append("Discount (%s%%): -%s" % (_percent(discount_pct), _money(discount)))
    lines.append("Tax (%s%%): %s" % (_percent(tax_pct), _money(tax)))
    lines.append("Total: %s" % _money(total))
    return "\n".join(lines)
