"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed team APIs:
  VALUE_CONVENTIONS v2: money is decimal.Decimal dollars (quantized to cents,
      ROUND_HALF_UP); rates are fractions (0.10 = 10%, 0.0825 = 8.25%);
      lookups return defaults on a miss.
  PRICING_API v2 (pricing.py): has_sku, get_unit_price, get_item_category,
      has_customer, get_customer_name, get_customer_discount, get_customer_region.
  TAX_API v2 (tax.py): calculate_tax(region, discount, lines) -> Decimal,
      tax_rate(region) -> Decimal fraction.

This module computes no tax rules: taxable base and rates come from tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _cents(amount):
    """Round a Decimal dollar amount to the cent, half up."""
    return Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal dollar amount as $12.50."""
    return "$" + format(_cents(amount), "f")


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros: 0.0825 -> '8.25'."""
    pct = Decimal(fraction) * 100
    return format(pct.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    lines_in = order["lines"]

    # Customer information. Unknown customers: shown by id, 0% discount, 0% tax.
    if pricing.has_customer(customer_id):
        customer_name = pricing.get_customer_name(customer_id)
        discount = Decimal(pricing.get_customer_discount(customer_id))
        region = pricing.get_customer_region(customer_id)
    else:
        customer_name = customer_id
        discount = Decimal("0")
        region = ""

    out = [f"Customer: {customer_name}"]

    # Item lines. Unknown skus are listed in place and skipped in the totals.
    subtotal = Decimal("0")
    taxable_lines = []  # (category, line_amount) for tax.py
    for sku, qty in lines_in:
        if not pricing.has_sku(sku):
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = Decimal(pricing.get_unit_price(sku))
        amount = _cents(unit_price * qty)
        subtotal += amount
        out.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}")
        taxable_lines.append((pricing.get_item_category(sku), amount))

    # Discount: subtotal * discount fraction, rounded to the cent, half up.
    discount_amount = _cents(subtotal * discount)

    # Tax: computed by tax.py. A customer with no region pays no tax.
    if region:
        tax_amount = Decimal(tax.calculate_tax(region, discount, taxable_lines))
        tax_fraction = Decimal(tax.tax_rate(region))
    else:
        tax_amount = Decimal("0")
        tax_fraction = Decimal("0")

    total = subtotal - discount_amount + _cents(tax_amount)

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount)}%): -{_money(discount_amount)}")
    out.append(f"Tax ({_percent(tax_fraction)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")

    return "\n".join(out)
