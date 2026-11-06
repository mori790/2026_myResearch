"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).

Pricing API (agreed with agent1, decision pricing_api v1):
  pricing.unit_price_cents(sku) -> int cents, or None if the SKU is unknown
  pricing.get_customer(customer_id) -> {"name", "discount_percent", "tax_percent"}
                                       (percents are Decimal, e.g. Decimal("8.25")),
                                       or None if the customer is unknown
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing


def _round_cents(value):
    """Round a Decimal number of cents to a whole cent, half up."""
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format a non-negative integer number of cents as $X.YY."""
    return "${}.{:02d}".format(cents // 100, cents % 100)


def _percent(value):
    """Format a Decimal percent without trailing zeros (10, 8.25, 0)."""
    return format(value.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: show the id, no discount, no tax.
        name = customer_id
        discount_percent = Decimal(0)
        tax_percent = Decimal(0)
    else:
        name = customer["name"]
        discount_percent = Decimal(str(customer["discount_percent"]))
        tax_percent = Decimal(str(customer["tax_percent"]))

    lines = ["Customer: {}".format(name)]
    subtotal = 0
    for sku, quantity in order["lines"]:
        unit_price = pricing.unit_price_cents(sku)
        if unit_price is None:
            lines.append("UNKNOWN SKU: {}".format(sku))
            continue
        amount = unit_price * quantity
        subtotal += amount
        lines.append("{} x{} @ {} = {}".format(
            sku, quantity, _money(unit_price), _money(amount)))

    discount = _round_cents(Decimal(subtotal) * discount_percent / 100)
    taxable = subtotal - discount
    tax = _round_cents(Decimal(taxable) * tax_percent / 100)
    total = taxable + tax

    lines.append("Subtotal: {}".format(_money(subtotal)))
    lines.append("Discount ({}%): -{}".format(
        _percent(discount_percent), _money(discount)))
    lines.append("Tax ({}%): {}".format(_percent(tax_percent), _money(tax)))
    lines.append("Total: {}".format(_money(total)))
    return "\n".join(lines)
