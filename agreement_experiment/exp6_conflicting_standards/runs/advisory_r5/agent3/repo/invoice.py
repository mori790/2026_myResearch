"""Invoice module. Owned by agent3. Implement render_invoice(order).

Decisions used (committed in the shared decision log):
  - MONEY_REPRESENTATION v2: money is integer cents (1250 = $12.50).
  - PERCENT_REPRESENTATION v2: percent numbers (10 means 10%).
  - MISSING_LOOKUP_RESULT v1: pricing returns None for unknown ids.
  - PRICING_API v2: get_item(sku) -> {sku, name, unit_price_cents, category} or None;
                    get_customer(id) -> {id, name, discount_pct, region} or None.
  - tax.api v3: compute_tax_cents(lines, region, discount_pct) -> int cents;
                tax_rate(region) -> percent number for display.
  - tax.unknown_customer v1: region None means unknown customer.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as dollars: 1250 -> '$12.50', 0 -> '$0.00'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def _discount_cents(subtotal_cents, discount_pct):
    """Discount in integer cents: subtotal * pct / 100, rounded half up to the cent."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, region None means 0% tax.
        name = customer_id
        discount_pct = 0
        region = None
    else:
        name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    line_texts = []
    tax_lines = []
    subtotal_cents = 0
    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            line_texts.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = item["unit_price_cents"]
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        line_texts.append(f"{sku} x{qty} @ {_money(unit_cents)} = {_money(amount_cents)}")
        tax_lines.append({"category": item["category"], "amount_cents": amount_cents})

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    # tax.py applies the discount to taxable lines itself (tax.api v3).
    tax_cents = tax.compute_tax_cents(tax_lines, region, discount_pct)
    tax_pct = tax.tax_rate(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out = [f"Customer: {name}"]
    out.extend(line_texts)
    out.append(f"Subtotal: {_money(subtotal_cents)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount_cents)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_cents)}")
    out.append(f"Total: {_money(total_cents)}")
    return "\n".join(out)
