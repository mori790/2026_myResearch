"""Invoice module. Owned by agent3. Implement render_invoice(order).

Boundary with the other modules (committed decisions pricing_api v1, tax_api v2):
  pricing.get_item(sku)                -> dict {sku, name, price (float $), category} or None
  pricing.get_customer(id)             -> dict {id, name, discount (fraction), region} or None
  tax.get_tax(region, lines, discount) -> [tax_amount (float $), tax_rate (fraction)]
      lines = [[category, line_amount (float $)], ...] for all known items, in order
      region = None for an unknown customer (no tax)

This module does no tax-rule computation; it only calls tax.get_tax and displays the result.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_decimal(value):
    """Convert a float (or int/str) from another module to Decimal via its shortest repr."""
    return Decimal(str(value))


def _round_cent(amount):
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal dollar amount as $12.50 (amount already rounded to the cent)."""
    return "${:.2f}".format(amount)


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros: 0.1 -> '10', 0.0825 -> '8.25', 0 -> '0'."""
    percent = _to_decimal(fraction) * 100
    return format(percent.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_name = customer_id
        region = None
        discount_fraction = Decimal("0")
    else:
        customer_name = customer["name"]
        region = customer["region"]
        discount_fraction = _to_decimal(customer["discount"])

    output_lines = ["Customer: {}".format(customer_name)]
    subtotal = Decimal("0.00")
    tax_lines = []  # [category, line_amount] for known items, passed to tax.get_tax

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output_lines.append("UNKNOWN SKU: {}".format(sku))
            continue

        unit_price = _round_cent(_to_decimal(item["price"]))
        line_amount = _round_cent(unit_price * quantity)
        subtotal += line_amount
        tax_lines.append([item["category"], float(line_amount)])
        output_lines.append("{} x{} @ {} = {}".format(
            sku, quantity, _money(unit_price), _money(line_amount)))

    discount = _round_cent(subtotal * discount_fraction)

    tax_amount, tax_rate = tax.get_tax(
        region, tax_lines, float(discount_fraction))
    tax_amount = _round_cent(_to_decimal(tax_amount))

    total = subtotal - discount + tax_amount

    output_lines.append("Subtotal: {}".format(_money(subtotal)))
    output_lines.append("Discount ({}%): -{}".format(
        _percent(discount_fraction), _money(discount)))
    output_lines.append("Tax ({}%): {}".format(
        _percent(tax_rate), _money(tax_amount)))
    output_lines.append("Total: {}".format(_money(total)))

    return "\n".join(output_lines)
