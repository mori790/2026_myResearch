"""Invoice module. Owned by agent3. Implement render_invoice(order).

API conventions (see decision log PRICING_API and TAX_API):
- pricing.py returns float dollars and fractional discounts (0.10 = 10%).
- tax.py takes int cents and percent numbers (10 = 10%).
- This module converts at its boundary and keeps all money as int cents.
- Tax rules are not computed here; they come from tax.py.
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(dollars):
    """Convert a dollar amount (float, str or Decimal) to int cents, half up."""
    return int((Decimal(str(dollars)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format non-negative int cents as '12.50' (no dollar sign)."""
    return f"{cents // 100}.{cents % 100:02d}"


def _percent_text(pct):
    """Format a Decimal percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(pct)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        customer_name = customer_id
        discount_frac = Decimal(0)
        region = None
    else:
        customer_name = customer.name
        discount_frac = Decimal(str(customer.discount))
        region = customer.region

    out = [f"Customer: {customer_name}"]
    taxable_lines = []  # (category, amount_cents) pairs for tax.py
    subtotal = 0

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = _to_cents(item.price)
        amount = unit * qty
        subtotal += amount
        taxable_lines.append((item.category, amount))
        out.append(f"{sku} x{qty} @ ${_money(unit)} = ${_money(amount)}")

    discount_cents = int(
        (Decimal(subtotal) * discount_frac).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    discount_pct = discount_frac * 100

    if region is None:
        tax_pct = Decimal(0)
    else:
        tax_pct = Decimal(str(tax.tax_rate_pct(region)))
    tax_cents = tax.calculate_tax(
        taxable_lines, region, discount_pct=float(discount_pct)
    )

    total = subtotal - discount_cents + tax_cents

    out.append(f"Subtotal: ${_money(subtotal)}")
    out.append(f"Discount ({_percent_text(discount_pct)}%): -${_money(discount_cents)}")
    out.append(f"Tax ({_percent_text(tax_pct)}%): ${_money(tax_cents)}")
    out.append(f"Total: ${_money(total)}")
    return "\n".join(out)
