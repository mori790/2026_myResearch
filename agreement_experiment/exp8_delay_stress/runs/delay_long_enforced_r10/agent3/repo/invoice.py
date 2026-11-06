"""Invoice module. Owned by agent3. Implement render_invoice(order).

Agreed interface (committed in the shared agreement log):
  pricing.get_item(sku)        -> {sku, name, unit_price_cents: int, category} or None
  pricing.get_customer(cid)    -> {customer_id, name, discount_pct: number, region} or None
  tax.compute_tax(region, lines, discount_pct) -> int cents
      lines = [{"category": str, "amount_cents": int}, ...]
  tax.tax_pct(region)          -> number (e.g. 8.25)

All money is integer cents. Percents are plain numbers (10 = 10%).
Tax rules are NOT computed here; this module only calls tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as dollars: 1250 -> '$12.50'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * discount_pct / 100, rounded to the cent (half up)."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(exact.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, no region (0% tax from tax.py).
        name = customer_id
        discount_pct = 0
        region = None
    else:
        name = customer["name"] or customer_id
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out_lines = [f"Customer: {name}"]
    taxable_lines = []  # known lines only, before discount, for tax.py
    subtotal_cents = 0

    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = item["unit_price_cents"]
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        out_lines.append(f"{sku} x{qty} @ {_money(unit_cents)} = {_money(amount_cents)}")
        taxable_lines.append({"category": item["category"], "amount_cents": amount_cents})

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    tax_cents = tax.compute_tax(region, taxable_lines, discount_pct)
    tax_rate = tax.tax_pct(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append(f"Subtotal: {_money(subtotal_cents)}")
    out_lines.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount_cents)}")
    out_lines.append(f"Tax ({_percent(tax_rate)}%): {_money(tax_cents)}")
    out_lines.append(f"Total: {_money(total_cents)}")

    return "\n".join(out_lines)
