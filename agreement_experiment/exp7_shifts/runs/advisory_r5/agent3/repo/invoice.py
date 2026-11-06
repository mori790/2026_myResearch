"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed decisions:
  pricing_api v1: get_item(sku), get_customer(id) (floats in dollars, discount as fraction)
  tax_api v1:     calculate_tax(lines, region, discount) (undiscounted amounts in, tax out)
  tax_api_rate v1: get_tax_rate(region) (fraction, for display only)
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(value):
    """Decimal dollars -> '$12.50' (values are already rounded to the cent)."""
    return "${:.2f}".format(value)


def _to_cents(value):
    """Round a Decimal to the cent, half up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _from_float(value):
    """Convert a float dollar amount from pricing/tax to Decimal without float noise."""
    return Decimal(str(value))


def _percent(fraction):
    """Fraction -> percent text without trailing zeros: 0.10 -> '10', 0.0825 -> '8.25', 0 -> '0'."""
    pct = (_from_float(fraction) * 100).normalize()
    return "{:f}".format(pct)


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, no discount, no tax.
        discount_fraction = Decimal("0")
        region = None
    else:
        discount_fraction = _from_float(customer["discount"])
        region = customer["region"]

    out = ["Customer: {}".format(customer["name"] if customer is not None else customer_id)]

    subtotal = Decimal("0")
    tax_lines = []  # undiscounted line totals for tax.py

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: {}".format(sku))
            continue

        unit_price = _from_float(item["price"])
        line_amount = _to_cents(unit_price * quantity)
        subtotal += line_amount
        tax_lines.append({"category": item["category"], "amount": float(line_amount)})

        out.append("{} x{} @ {} = {}".format(
            sku, quantity, _money(_to_cents(unit_price)), _money(line_amount)))

    discount = _to_cents(subtotal * discount_fraction)
    tax_amount = _to_cents(_from_float(tax.calculate_tax(tax_lines, region, float(discount_fraction))))
    tax_percent = _percent(tax.get_tax_rate(region))
    total = subtotal - discount + tax_amount

    out.append("Subtotal: {}".format(_money(subtotal)))
    out.append("Discount ({}%): -{}".format(_percent(discount_fraction), _money(discount)))
    out.append("Tax ({}%): {}".format(tax_percent, _money(tax_amount)))
    out.append("Total: {}".format(_money(total)))

    return "\n".join(out)
