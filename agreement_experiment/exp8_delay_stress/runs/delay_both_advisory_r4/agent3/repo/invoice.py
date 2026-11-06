"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed team decisions:
  pricing_api v2 : get_item(sku) -> dict {sku, name, price_cents, category} or None
                   get_customer(cid) -> dict {id, name, discount_pct, region} or None
                   (money in integer cents, discount_pct as a percent number, 10 = 10%)
  tax_api v1     : compute_tax(lines, region, discount_pct=0) -> int cents
                   lines = list of (category, amount_cents) for all known line items
                   tax_rate(region) -> percent number (8.25 etc.), None -> 0

This module does no tax rule work; it only calls pricing and tax.
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
    if value is None:
        value = 0
    text = format(Decimal(str(value)).normalize(), "f")
    return text


def _half_up_discount(subtotal_cents, discount_pct):
    """Discount in integer cents = subtotal * pct / 100, rounded half up to the cent."""
    raw = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_label = customer_id
        discount_pct = 0
        region = None
    else:
        customer_label = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    lines_out = [f"Customer: {customer_label}"]
    subtotal_cents = 0
    taxable_lines = []  # (category, amount_cents) for known items only

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            lines_out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = item["price_cents"]
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        taxable_lines.append((item["category"], amount_cents))
        lines_out.append(
            f"{sku} x{qty} @ {_money(unit_cents)} = {_money(amount_cents)}"
        )

    discount_cents = _half_up_discount(subtotal_cents, discount_pct)
    tax_cents = tax.compute_tax(taxable_lines, region, discount_pct)
    tax_rate = tax.tax_rate(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    lines_out.append(f"Subtotal: {_money(subtotal_cents)}")
    lines_out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount_cents)}")
    lines_out.append(f"Tax ({_percent(tax_rate)}%): {_money(tax_cents)}")
    lines_out.append(f"Total: {_money(total_cents)}")

    return "\n".join(lines_out)
