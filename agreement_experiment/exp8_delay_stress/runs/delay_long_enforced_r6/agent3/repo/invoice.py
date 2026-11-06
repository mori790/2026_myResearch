"""Invoice module. Owned by agent3. Implement render_invoice(order).

Interfaces used (committed in the shared decision log):
  pricing.item_exists(sku) -> bool
  pricing.unit_price(sku) -> int cents | None
  pricing.item_category(sku) -> str | None
  pricing.customer_name(cid) -> str | None
  pricing.customer_region(cid) -> str | None
  pricing.customer_discount_pct(cid) -> int percent (0 for unknown customer)
  tax.tax_pct(region) -> Decimal percent
  tax.compute_tax(region, lines, discount_pct) -> int cents
    lines = [(category, amount_cents), ...]

Money is handled as integer cents here (matches pricing and tax);
the only Decimal arithmetic is the half-up rounding of the discount.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format non-negative int cents as dollars: 1250 -> '$12.50'."""
    return "$%d.%02d" % (cents // 100, cents % 100)


def _percent(value):
    """Format a percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * percent / 100, rounded to the cent, half up."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(exact.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]

    # Customer information (unknown customer: shown by id, 0% discount, 0% tax).
    customer_name = pricing.customer_name(customer_id)
    label = customer_name if customer_name else customer_id
    region = pricing.customer_region(customer_id)
    discount_pct = pricing.customer_discount_pct(customer_id)

    # Item lines. Unknown skus are listed in place and skipped in totals and tax.
    out_lines = ["Customer: %s" % label]
    subtotal = 0
    tax_lines = []
    for sku, quantity in order["lines"]:
        if not pricing.item_exists(sku):
            out_lines.append("UNKNOWN SKU: %s" % sku)
            continue
        unit = pricing.unit_price(sku)
        amount = unit * quantity
        subtotal += amount
        out_lines.append("%s x%d @ %s = %s" % (sku, quantity, _money(unit), _money(amount)))
        tax_lines.append((pricing.item_category(sku), amount))

    # Discount is computed here; tax (and its discount handling) comes from tax.py.
    discount = _discount_cents(subtotal, discount_pct)

    # Tax amount and rate come from tax.py. No region means no tax (rate 0%).
    tax_amount = tax.compute_tax(region, tax_lines, discount_pct)
    if region is None:
        tax_rate = Decimal(0)
    else:
        tax_rate = tax.tax_pct(region)

    total = subtotal - discount + tax_amount

    out_lines.append("Subtotal: %s" % _money(subtotal))
    out_lines.append("Discount (%s%%): -%s" % (_percent(discount_pct), _money(discount)))
    out_lines.append("Tax (%s%%): %s" % (_percent(tax_rate), _money(tax_amount)))
    out_lines.append("Total: %s" % _money(total))

    return "\n".join(out_lines)
