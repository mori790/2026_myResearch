"""Invoice module. Owned by agent3. Implement render_invoice(order).

Conforms to the team decisions:
  - pricing_api v1: get_item(sku), get_customer(id); money = float dollars,
    discount_rate = fraction (0.10 = 10%).
  - tax_api v1: compute_tax(lines, region, discount_pct) -> int cents,
    tax_pct(region) -> percent number; money = int cents, percent = number (8.25).

All tax rules live in tax.py. This module only converts units at the boundary,
does the invoice arithmetic, and formats the output.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(dollars):
    """Convert a float (or str/Decimal) dollar amount to int cents, half up."""
    value = (Decimal(str(dollars)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(value)


def _round_cents(value):
    """Round a Decimal amount in cents to an int, half up."""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _fmt_money(cents):
    """Format non-negative int cents as '$12.50'. Sign is handled by the caller."""
    cents = abs(cents)
    return "$%d.%02d" % (cents // 100, cents % 100)


def _fmt_percent(percent):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25'."""
    text = format(Decimal(str(percent)).normalize(), "f")
    return text


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_rate = 0.0
        region = None
    else:
        customer_name = customer.name
        discount_rate = customer.discount_rate
        region = customer.region

    lines_out = ["Customer: %s" % customer_name]

    subtotal_cents = 0
    taxable_lines = []  # (category, amount_cents) for tax.py

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            lines_out.append("UNKNOWN SKU: %s" % sku)
            continue

        unit_cents = _to_cents(item.price)
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        taxable_lines.append((item.category, amount_cents))

        lines_out.append("%s x%d @ %s = %s" % (
            sku, quantity, _fmt_money(unit_cents), _fmt_money(amount_cents)))

    # Discount: subtotal * discount rate, rounded to the cent (half up).
    rate = Decimal(str(discount_rate))
    discount_cents = _round_cents(Decimal(subtotal_cents) * rate)
    discount_pct = round(discount_rate * 100, 6)

    # Tax amount and tax percent come from tax.py.
    if region is None:
        tax_cents = 0
        tax_percent = 0
    else:
        tax_cents = tax.compute_tax(taxable_lines, region, discount_pct)
        tax_percent = tax.tax_pct(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    lines_out.append("Subtotal: %s" % _fmt_money(subtotal_cents))
    lines_out.append("Discount (%s%%): -%s" % (
        _fmt_percent(discount_pct), _fmt_money(discount_cents)))
    lines_out.append("Tax (%s%%): %s" % (
        _fmt_percent(tax_percent), _fmt_money(tax_cents)))
    lines_out.append("Total: %s" % _fmt_money(total_cents))

    return "\n".join(lines_out)
