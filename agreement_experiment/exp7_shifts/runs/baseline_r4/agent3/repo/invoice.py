"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the agreed APIs (see agreement log PRICING_API and TAX_API):
  pricing.get_customer(id) -> {id, name, discount (fraction), region} | None
  pricing.get_item(sku)    -> {sku, name, price (float dollars), category} | None
  tax.get_tax_pct(region)  -> float percent; None -> 0.0
  tax.compute_tax(lines=[(category, amount_cents)], region, discount_pct)
                           -> int cents (lines are pre-discount)

Internally all money is decimal.Decimal in dollars (team standard). Values coming
from pricing/tax are converted through repr() so that e.g. 0.07 becomes exactly
Decimal('0.07') instead of a binary-float approximation.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dec(value):
    """Exact Decimal for a float/int coming from another module."""
    return Decimal(repr(value))


def _to_cents(amount):
    """Decimal dollars -> int cents, rounded half up."""
    return int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))


def _money(amount):
    """Format a non-negative Decimal dollar amount as $12.50."""
    return "$" + format(amount.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def _percent(value):
    """Format a percent without trailing zeros: 10, 8.25, 0."""
    return format(value.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None -> tax 0).
        name = customer_id
        discount_pct = Decimal(0)
        region = None
    else:
        name = customer["name"]
        discount_pct = _dec(customer["discount"]) * 100
        region = customer.get("region")

    out = [f"Customer: {name}"]
    subtotal = Decimal(0)
    tax_lines = []  # (category, amount_cents), pre-discount, for tax.compute_tax

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _dec(item["price"])
        amount = unit_price * qty
        subtotal += amount
        tax_lines.append((item["category"], _to_cents(amount)))
        out.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}")

    discount = (subtotal * discount_pct / 100).quantize(CENT, rounding=ROUND_HALF_UP)

    # Tax rules live in tax.py; the discount percent is passed in as a number.
    tax_amount = Decimal(tax.compute_tax(tax_lines, region, float(discount_pct))) / 100
    tax_pct = _dec(tax.get_tax_pct(region))

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
