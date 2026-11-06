"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed team decisions:
  - money_unit v2: amounts are decimal.Decimal dollars; quantized to 0.01
    (ROUND_HALF_UP) only for the discount and the final amounts shown.
  - percent_unit v1: percentages are fractions (10% -> 0.10).
  - lookup_miss v1: pricing.get_item / pricing.get_customer return None on a miss.
  - pricing_api v2: get_item(sku) -> {sku, name, unit_price, category} or None;
                    get_customer(id) -> {id, name, discount_rate, region} or None.
  - tax_api v3: tax.get_tax(region, discount_rate, lines) -> (tax_rate, tax_amount),
                lines = [(category, undiscounted_amount), ...].
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ZERO = Decimal("0")


def _quantize(amount):
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal dollar amount as e.g. '$12.50' (no sign handling)."""
    return "$" + format(_quantize(amount), "f")


def _signed_money(amount):
    """Format a non-negative amount as a deduction, e.g. '-$3.91'."""
    return "-" + _money(amount)


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros: 0.0825 -> '8.25%', 0 -> '0%'."""
    value = Decimal(fraction) * 100
    text = format(value.normalize(), "f")
    if text == "-0":
        text = "0"
    return text + "%"


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (tax.py handles region None).
        customer_name = customer_id
        region = None
        discount_rate = ZERO
    else:
        customer_name = customer["name"]
        region = customer["region"]
        discount_rate = Decimal(customer["discount_rate"])

    out_lines = [f"Customer: {customer_name}"]
    subtotal = ZERO
    tax_lines = []  # (category, undiscounted amount) for known items only

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = Decimal(item["unit_price"])
        amount = unit_price * quantity
        subtotal += amount
        tax_lines.append((item["category"], amount))
        out_lines.append(f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}")

    discount = _quantize(subtotal * discount_rate)
    tax_rate, tax_amount = tax.get_tax(region, discount_rate, tax_lines)
    tax_amount = _quantize(Decimal(tax_amount))
    total = subtotal - discount + tax_amount

    out_lines.append(f"Subtotal: {_money(subtotal)}")
    out_lines.append(f"Discount ({_percent(discount_rate)}): {_signed_money(discount)}")
    out_lines.append(f"Tax ({_percent(tax_rate)}): {_money(tax_amount)}")
    out_lines.append(f"Total: {_money(total)}")

    return "\n".join(out_lines)
