"""Invoice module. Owned by agent3. Implement render_invoice(order).

All item, customer and tax information comes from pricing.py and tax.py.
This module does not compute tax rules itself.

Money: decimal.Decimal dollars. Percentages: multipliers (0.90 = 10% off).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def _money(amount):
    """Format a Decimal as '$12.50' (negative as '-$3.91')."""
    amount = amount.quantize(CENT, rounding=ROUND_HALF_UP)
    if amount < 0:
        return "-$" + format(-amount, "f")
    return "$" + format(amount, "f")


def _percent(multiplier):
    """Turn a multiplier into a percent string.

    Examples: 1.0825 -> '8.25'; 0.90 -> '10'; 1 -> '0'.
    Trailing zeros are removed so the output has no trailing zeros.
    """
    value = (multiplier * HUNDRED).normalize()
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _discount_percent(discount_multiplier):
    """Discount percent from a price multiplier: 0.90 -> 10."""
    return _percent(ONE - discount_multiplier)


def _tax_percent(tax_multiplier):
    """Tax percent from a tax multiplier: 1.0825 -> 8.25."""
    return _percent(tax_multiplier - ONE)


def render_invoice(order):
    customer_id = order["customer"]
    customer_label = pricing.customer_name(customer_id) or customer_id

    lines = ["Customer: " + customer_label]

    subtotal = Decimal("0")
    for sku, quantity in order["lines"]:
        if not pricing.has_sku(sku):
            lines.append("UNKNOWN SKU: " + sku)
            continue
        unit_price = pricing.unit_price(sku)
        amount = unit_price * quantity
        subtotal += amount
        lines.append(
            "{} x{} @ {} = {}".format(sku, quantity, _money(unit_price), _money(amount))
        )

    discount_multiplier = pricing.discount_multiplier(customer_id)
    discount = (subtotal * (ONE - discount_multiplier)).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    taxable = subtotal - discount

    tax_amount, tax_multiplier = tax.tax_for(customer_id, taxable)
    tax_amount = tax_amount.quantize(CENT, rounding=ROUND_HALF_UP)

    total = subtotal - discount + tax_amount

    lines.append("Subtotal: " + _money(subtotal))
    lines.append(
        "Discount ({}%): -{}".format(_discount_percent(discount_multiplier), _money(discount))
    )
    lines.append("Tax ({}%): {}".format(_tax_percent(tax_multiplier), _money(tax_amount)))
    lines.append("Total: " + _money(total))

    return "\n".join(lines)
