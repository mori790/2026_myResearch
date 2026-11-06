"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed decisions:
  pricing_api v1: pricing.get_item(sku) -> dict or None;
                  pricing.get_customer(id) -> dict or None.
                  Money is int cents; discount_pct is a percent number (10 = 10%).
  tax_api v2:     tax.compute_tax(lines, region, discount_pct) -> int cents;
                  tax.rate_percent(region) -> Decimal percent (e.g. Decimal("8.25")).
This module does not compute any tax rule itself.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format a non-negative integer cent amount as dollars: 1250 -> '$12.50'."""
    return f"${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = format(Decimal(str(value)), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _discount_cents(subtotal_cents, discount_pct):
    """Discount = subtotal * percent / 100, rounded to the cent (half up)."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    """Return the invoice text for an order {"customer": id, "lines": [[sku, qty], ...]}."""
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        name = customer_id
        discount_pct = 0
        region = None
    else:
        name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out = [f"Customer: {name}"]
    subtotal_cents = 0
    taxable_lines = []
    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = item["unit_price_cents"]
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        out.append(f"{sku} x{qty} @ {_money(unit_cents)} = {_money(amount_cents)}")
        taxable_lines.append({"category": item["category"], "amount_cents": amount_cents})

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    tax_cents = tax.compute_tax(taxable_lines, region, discount_pct)
    tax_rate = tax.rate_percent(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append(f"Subtotal: {_money(subtotal_cents)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount_cents)}")
    out.append(f"Tax ({_percent(tax_rate)}%): {_money(tax_cents)}")
    out.append(f"Total: {_money(total_cents)}")
    return "\n".join(out)
