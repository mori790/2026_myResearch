"""Invoice module. Owned by agent3. Implement render_invoice(order).

Units of the committed team APIs:
  pricing_api v1: money = float dollars, percent = float fraction (0.10 = 10%), miss = None
  tax_api v1:     money = int cents,     percent = number (8.25 = 8.25%)
This module converts between the two units. It does not compute tax rules itself:
tax comes from tax.compute_tax().
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(dollars):
    """float dollars -> int cents, rounded half up. Goes through repr() to avoid float error."""
    value = Decimal(repr(float(dollars))) * 100
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _fraction_to_percent(fraction):
    """float fraction (0.1) -> Decimal percent (10)."""
    return Decimal(repr(float(fraction))) * 100


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * percent / 100, rounded to the cent (half up). Returns non-negative int cents."""
    value = Decimal(subtotal_cents) * discount_pct / 100
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """int cents -> '$12.50'. Negative values get a leading minus sign before the dollar sign."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0.0 -> '0'."""
    return format(Decimal(repr(float(value))).normalize(), "f")


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None).
        name = customer_id
        discount_pct = Decimal(0)
        region = None
    else:
        name = customer.get("name", customer_id)
        discount_pct = _fraction_to_percent(customer.get("discount", 0.0))
        region = customer.get("region")

    out = [f"Customer: {name}"]
    taxable_lines = []  # dicts {amount_cents, category} for tax.compute_tax
    subtotal = 0

    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = _to_cents(item["price"])
        amount = unit_cents * qty
        subtotal += amount
        taxable_lines.append({"amount_cents": amount, "category": item.get("category", "")})
        out.append(f"{sku} x{qty} @ {_money(unit_cents)} = {_money(amount)}")

    discount = _discount_cents(subtotal, discount_pct)
    # tax.py applies the discount percent to the taxable base itself.
    tax_result = tax.compute_tax(taxable_lines, region, discount_pct=float(discount_pct))
    tax_cents = tax_result["tax_cents"]
    tax_pct = tax_result["rate_pct"]
    total = subtotal - discount + tax_cents

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_cents)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
