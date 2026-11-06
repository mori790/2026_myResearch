"""Invoice module. Owned by agent3.

render_invoice(order) builds the plain-text invoice. All item, customer and
tax information comes from pricing.py (get_item, get_customer) and tax.py
(tax_for). This module does not compute tax rules itself.

Committed team conventions (PRICING_API v1, TAX_API v1):
  - pricing and tax exchange floats in dollars; discounts and tax rates are
    fractions (0.10 = 10%); a missing lookup returns None.
  - Inside this module, money is handled as decimal.Decimal dollars.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(amount):
    """Format a non-negative Decimal dollar amount as '$12.50'."""
    return "$" + str(amount.quantize(CENT, rounding=ROUND_HALF_UP))


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros.

    0.10 -> '10', 0.0825 -> '8.25', 0.0 -> '0'.
    """
    value = Decimal(str(round(float(fraction) * 100, 6)))
    return format(value.normalize(), "f")


def _to_decimal(value):
    """Convert a float from pricing/tax to Decimal via its shortest repr."""
    return Decimal(str(value))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None).
        customer_name = customer_id
        region = None
        discount_fraction = 0.0
    else:
        customer_name = customer.name
        region = customer.region
        discount_fraction = customer.discount

    out_lines = [f"Customer: {customer_name}"]

    # (amount, category) for each known line, as tax.py expects.
    tax_input_lines = []
    subtotal = Decimal("0")

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _to_decimal(item.price)
        amount = unit_price * quantity
        subtotal += amount
        out_lines.append(
            f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}"
        )
        tax_input_lines.append((float(amount), item.category))

    # Discount is shown rounded to the cent (half up) and subtracted from
    # the subtotal; tax.py applies the same discount to the taxable base.
    discount = (subtotal * _to_decimal(discount_fraction)).quantize(
        CENT, rounding=ROUND_HALF_UP
    )

    result = tax.tax_for(tax_input_lines, region, float(discount_fraction))
    tax_amount = _to_decimal(result.tax_amount).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    tax_rate = result.tax_rate

    total = subtotal - discount + tax_amount

    out_lines.append(f"Subtotal: {_money(subtotal)}")
    out_lines.append(
        f"Discount ({_percent(discount_fraction)}%): -{_money(discount)}"
    )
    out_lines.append(f"Tax ({_percent(tax_rate)}%): {_money(tax_amount)}")
    out_lines.append(f"Total: {_money(total)}")

    return "\n".join(out_lines)
