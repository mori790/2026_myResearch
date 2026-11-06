"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _round_cent(amount):
    """Round a Decimal amount to the cent, half up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a non-negative Decimal amount as $X.XX."""
    return "$" + format(_round_cent(amount), ".2f")


def _percent(value):
    """Format a Decimal percent without trailing zeros, e.g. 10, 8.25, 0."""
    return format(value.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: show the id, no discount, no tax.
        customer_name = customer_id
        discount_percent = Decimal("0")
        tax_percent = Decimal("0")
    else:
        customer_name = customer["name"]
        discount_percent = customer["discount_percent"]
        tax_percent = customer["tax_percent"]

    lines = ["Customer: " + customer_name]
    subtotal = Decimal("0")

    for sku, quantity in order["lines"]:
        unit_price = pricing.get_unit_price(sku)
        if unit_price is None:
            lines.append("UNKNOWN SKU: " + sku)
            continue
        amount = _round_cent(unit_price * quantity)
        subtotal += amount
        lines.append(
            "%s x%d @ %s = %s" % (sku, quantity, _money(unit_price), _money(amount))
        )

    discount = _round_cent(subtotal * discount_percent / HUNDRED)
    taxable = subtotal - discount
    tax = _round_cent(taxable * tax_percent / HUNDRED)
    total = subtotal - discount + tax

    lines.append("Subtotal: " + _money(subtotal))
    lines.append("Discount (%s%%): -%s" % (_percent(discount_percent), _money(discount)))
    lines.append("Tax (%s%%): %s" % (_percent(tax_percent), _money(tax)))
    lines.append("Total: " + _money(total))

    return "\n".join(lines)
