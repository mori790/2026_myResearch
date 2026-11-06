"""Invoice module. Owned by agent3. Implement render_invoice(order).

Shared decisions used here (committed in agree.py):
  - money_representation: integer cents at every module boundary (1250 = $12.50)
  - percent_representation: percent numbers at every module boundary (10 = 10%)
  - missing_lookup_return: pricing lookups return None on a miss
  - pricing_api v2: get_item(sku) -> {sku, name, price_cents, category} or None;
                    get_customer(customer_id) -> {id, name, discount_pct, region} or None
  - TAX_API v2: tax.compute_tax(region, discount_pct, lines) -> int cents, where lines
                are UNDISCOUNTED (category, amount_cents) pairs; tax.tax_rate(region) -> percent
  - UNKNOWN_CUSTOMER v1: an unknown customer is passed to tax with region None

This module does no tax computation itself. Discount is computed here (subtotal times
discount_pct, rounded half up to the cent). Tax is taken from tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _fmt_money(cents):
    """Format integer cents as dollars, e.g. 1250 -> '$12.50', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s$%d.%02d" % (sign, cents // 100, cents % 100)


def _fmt_percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = format(Decimal(str(value)).normalize(), "f")
    return text


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * discount_pct / 100, rounded half up to the cent."""
    amount = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, no tax region.
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out_lines = ["Customer: %s" % customer_name]
    tax_lines = []  # (category, amount_cents), undiscounted, for known skus only
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: %s" % sku)
            continue

        unit_cents = item["price_cents"]
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        tax_lines.append((item["category"], amount_cents))
        out_lines.append("%s x%d @ %s = %s" % (
            sku, quantity, _fmt_money(unit_cents), _fmt_money(amount_cents)))

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    tax_cents = tax.compute_tax(region, discount_pct, tax_lines)
    tax_rate = tax.tax_rate(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append("Subtotal: %s" % _fmt_money(subtotal_cents))
    out_lines.append("Discount (%s%%): -%s" % (
        _fmt_percent(discount_pct), _fmt_money(discount_cents)))
    out_lines.append("Tax (%s%%): %s" % (_fmt_percent(tax_rate), _fmt_money(tax_cents)))
    out_lines.append("Total: %s" % _fmt_money(total_cents))

    return "\n".join(out_lines)
