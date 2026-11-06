"""Invoice module. Owned by agent3. Implement render_invoice(order).

Agreed interfaces (committed in the shared decision log):
  PRICING_API v2:
    pricing.get_item(sku) -> {"sku", "name", "unit_price_cents": int, "category"} or None
    pricing.get_customer(customer_id) -> {"id", "name", "discount_pct": int, "region"} or None
  TAX_API v4:
    tax.sales_tax(region, discount_pct, lines) -> int cents
        lines = [(category, amount_cents), ...] for every known line (pre-discount)
    tax.tax_percent(region) -> percent number (e.g. 8.25)
  TAX_UNKNOWN_CUSTOMER v1:
    unknown customer -> region None, discount 0, tax 0.

All money is handled as int cents; percents are percent numbers (10 means 10%).
invoice.py does no tax rule computation itself.
"""

from decimal import Decimal

import pricing
import tax


def _money(cents):
    """Format int cents as dollars, e.g. 1250 -> '$12.50', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "{}${}.{:02d}".format(sign, cents // 100, cents % 100)


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = format(Decimal(str(value)).normalize(), "f")
    return text


def _round_half_up_div(numerator, denominator):
    """Integer division rounding half up (for non-negative numerator)."""
    return (numerator + denominator // 2) // denominator


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out = ["Customer: {}".format(customer_name)]
    known_lines = []  # (category, amount_cents) for every known line, pre-discount
    subtotal = 0

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: {}".format(sku))
            continue
        unit = item["unit_price_cents"]
        amount = unit * qty
        subtotal += amount
        known_lines.append((item["category"], amount))
        out.append("{} x{} @ {} = {}".format(sku, qty, _money(unit), _money(amount)))

    discount = _round_half_up_div(subtotal * discount_pct, 100)
    tax_cents = tax.sales_tax(region, discount_pct, known_lines)
    tax_pct = tax.tax_percent(region)
    total = subtotal - discount + tax_cents

    out.append("Subtotal: {}".format(_money(subtotal)))
    out.append("Discount ({}%): -{}".format(_percent(discount_pct), _money(discount)))
    out.append("Tax ({}%): {}".format(_percent(tax_pct), _money(tax_cents)))
    out.append("Total: {}".format(_money(total)))
    return "\n".join(out)
