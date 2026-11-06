"""Invoice rendering (agent3).

Implements the committed decision `module_api` v3 (agree.py):
  pricing.get_item(sku)            -> dict | None  (unit_price_cents, category, ...)
  pricing.get_customer(cid)        -> dict | None  (name, discount_pct, region, ...)
  tax.tax_rate(region)             -> percent number (8.25)
  tax.tax_amount(region, pct, lines) -> int cents; lines = [(category, line_cents), ...]

All money is handled as integer cents. Percent numbers are percents (10 = 10%).
This module does no tax-rule computation; it only calls pricing and tax.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as dollars, e.g. 1250 -> '$12.50'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = format(Decimal(str(value)).normalize(), "f")
    return text


def _round_half_up_cents(subtotal_cents, pct):
    """Return subtotal_cents * pct / 100 rounded half up to an integer number of cents."""
    exact = Decimal(subtotal_cents) * Decimal(str(pct)) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    """Render an order as the invoice text described in the task spec."""
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, and no region (tax.py returns 0).
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out_lines = [f"Customer: {customer_name}"]
    tax_lines = []  # (category, line_cents) for known skus only
    subtotal_cents = 0

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_cents = item["unit_price_cents"]
        line_cents = unit_cents * qty
        subtotal_cents += line_cents
        tax_lines.append((item["category"], line_cents))
        out_lines.append(f"{sku} x{qty} @ {_money(unit_cents)} = {_money(line_cents)}")

    discount_cents = _round_half_up_cents(subtotal_cents, discount_pct)
    tax_cents = tax.tax_amount(region, discount_pct, tax_lines)
    tax_rate = tax.tax_rate(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append(f"Subtotal: {_money(subtotal_cents)}")
    out_lines.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount_cents)}")
    out_lines.append(f"Tax ({_percent(tax_rate)}%): {_money(tax_cents)}")
    out_lines.append(f"Total: {_money(total_cents)}")

    return "\n".join(out_lines)
