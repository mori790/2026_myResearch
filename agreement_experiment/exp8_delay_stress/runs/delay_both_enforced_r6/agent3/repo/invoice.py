"""Invoice rendering.

All item, customer and tax data comes from pricing.py and tax.py (committed
decisions pricing-api v2 and tax_interface v3). This module does not compute
any tax rules itself.

Money handling: pricing and tax return float dollars and fraction percentages.
They are converted to Decimal via str() at the boundary, and all rounding is
done in Decimal (ROUND_HALF_UP, to the cent).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_decimal(value):
    """Convert a float (or int/str) returned by another module to Decimal."""
    return Decimal(str(value))


def _money(amount):
    """Format a Decimal dollar amount as e.g. '$12.50'."""
    cents = amount.quantize(CENT, rounding=ROUND_HALF_UP)
    return "$" + format(cents, ".2f")


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros.

    0.10 -> '10', 0.0825 -> '8.25', 0.0 -> '0'.
    """
    value = _to_decimal(fraction) * 100
    return format(value.normalize(), "f")


def render_invoice(order):
    """Render an order as an invoice string.

    order = {"customer": customer_id, "lines": [[sku, quantity], ...]}
    """
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, with 0% discount and 0% tax.
        name = customer_id
        discount = 0.0
        region = None
    else:
        name = customer.name
        discount = customer.discount
        region = customer.region

    out = [f"Customer: {name}"]

    subtotal = Decimal("0.00")
    taxable_lines = []  # (category, amount in float dollars), known items only
    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _to_decimal(item.price)
        amount = (unit_price * quantity).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += amount
        taxable_lines.append((item.category, float(amount)))
        out.append(f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}")

    discount_amount = (subtotal * _to_decimal(discount)).quantize(
        CENT, rounding=ROUND_HALF_UP
    )

    tax_amount = _to_decimal(
        tax.compute_tax(taxable_lines, region, discount)
    ).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_percent = _percent(tax.tax_rate(region))

    total = subtotal - discount_amount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount)}%): -{_money(discount_amount)}")
    out.append(f"Tax ({tax_percent}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")

    return "\n".join(out)
