"""Invoice module. Owned by agent3. Implement render_invoice(order).

Follows the committed team decisions:
  - money_percent_repr v1: money in integer cents (1250 = $12.50);
    percents as percent numbers (10 = 10%, 8.25 = 8.25%).
  - PRICING_API_V2 v1: pricing.get_item(sku) -> {sku, name, price_cents, category} or None;
    pricing.get_customer(customer_id) -> {id, name, discount_pct, region} or None.
  - tax_api v1: tax.compute_order_tax(lines, region, discount_pct) -> int cents, where
    lines = [(category, amount_cents)]; tax.tax_rate_pct(region) -> percent number.
  - unknown_customer v2: unknown customer -> region=None, 0% discount, 0% tax.

invoice.py does no tax rule computation; all tax comes from tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as dollars: 1250 -> '$12.50', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(pct):
    """Format a percent number without trailing zeros: 10 -> '10%', 8.25 -> '8.25%', 0 -> '0%'."""
    text = format(Decimal(str(pct)).normalize(), "f")
    return f"{text}%"


def _round_half_up_cents(subtotal_cents, discount_pct):
    """subtotal_cents * discount_pct / 100, rounded to the nearest cent (half up)."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_label = customer_id
        region = None
        discount_pct = 0
    else:
        customer_label = customer["name"]
        region = customer["region"]
        discount_pct = customer["discount_pct"]

    out_lines = [f"Customer: {customer_label}"]
    tax_lines = []  # (category, amount_cents) for known skus only, in order
    subtotal_cents = 0

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = item["price_cents"]
        line_cents = unit_cents * qty
        subtotal_cents += line_cents
        tax_lines.append((item["category"], line_cents))
        out_lines.append(
            f"{sku} x{qty} @ {_money(unit_cents)} = {_money(line_cents)}"
        )

    discount_cents = _round_half_up_cents(subtotal_cents, discount_pct)
    tax_cents = tax.compute_order_tax(tax_lines, region, discount_pct)
    if region is None:
        tax_pct = 0  # unknown customer: 0% tax, no rate lookup
    else:
        tax_pct = tax.tax_rate_pct(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append(f"Subtotal: {_money(subtotal_cents)}")
    out_lines.append(f"Discount ({_percent(discount_pct)}): -{_money(discount_cents)}")
    out_lines.append(f"Tax ({_percent(tax_pct)}): {_money(tax_cents)}")
    out_lines.append(f"Total: {_money(total_cents)}")

    return "\n".join(out_lines)
