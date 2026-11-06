"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed decisions pricing_api v2 and tax_api v1:
  - money: integer cents
  - percent: percent number (10 means 10%)
  - pricing.get_item(sku) -> dict or None
  - pricing.get_customer(customer_id) -> dict or None
  - tax.compute_tax_cents(region, lines, discount_pct) -> int cents
  - tax.tax_rate_pct(region) -> percent number

This module does no tax rule computation. Money is formatted from integer cents.
Percent arithmetic for the discount uses decimal.Decimal, rounded half up.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _fmt_money(cents):
    """Integer cents -> dollar string: 1250 -> '$12.50', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s$%d.%02d" % (sign, cents // 100, cents % 100)


def _fmt_percent(pct):
    """Percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(pct)).normalize(), "f")


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * discount_pct / 100, rounded to the cent, half up. Returns int cents."""
    value = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None).
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out_lines = ["Customer: %s" % customer_name]
    tax_lines = []  # {"category", "amount_cents"} for known skus only
    subtotal_cents = 0

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: %s" % sku)
            continue

        unit_cents = item["unit_price_cents"]
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        out_lines.append("%s x%d @ %s = %s" % (
            sku, qty, _fmt_money(unit_cents), _fmt_money(amount_cents)))
        tax_lines.append({"category": item["category"], "amount_cents": amount_cents})

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    tax_cents = tax.compute_tax_cents(region, tax_lines, discount_pct)
    tax_pct = tax.tax_rate_pct(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append("Subtotal: %s" % _fmt_money(subtotal_cents))
    out_lines.append("Discount (%s%%): -%s" % (_fmt_percent(discount_pct), _fmt_money(discount_cents)))
    out_lines.append("Tax (%s%%): %s" % (_fmt_percent(tax_pct), _fmt_money(tax_cents)))
    out_lines.append("Total: %s" % _fmt_money(total_cents))

    return "\n".join(out_lines)
