"""Invoice module. Owned by agent3. Implement render_invoice(order).

Committed interfaces used (see shared agreement log):
  pricing.get_item(sku) -> {"sku", "name", "price_cents": int, "category"}; KeyError if unknown
  pricing.get_customer(customer_id) -> {"id", "name", "discount_pct": float (10 = 10%), "region": str | None};
      KeyError if unknown
  tax.compute_tax_cents(lines, region, discount_pct) -> int cents
      lines = [{"amount_cents": int, "category": str}, ...]; region None -> 0
  tax.tax_pct(region) -> float percent (8.25 = 8.25%); KeyError if region unknown

Money is integer cents internally; Decimal is used only for exact percentage arithmetic.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as dollars, e.g. 1250 -> '$12.50'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(pct):
    """Format a percent number without trailing zeros, e.g. 10.0 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    d = Decimal(str(pct)).normalize()
    return f"{d:f}"


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * discount_pct / 100, rounded to the cent, half up (exact arithmetic)."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(exact.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]

    # Customer lookup. Unknown customer: shown by id, 0% discount, no region (0% tax).
    try:
        customer = pricing.get_customer(customer_id)
        name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]
    except KeyError:
        name = customer_id
        discount_pct = 0
        region = None

    out = [f"Customer: {name}"]

    # Line items. Unknown skus are listed in place and skipped from the totals.
    taxable_lines = []
    subtotal_cents = 0
    for sku, quantity in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = item["price_cents"]
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        taxable_lines.append({"amount_cents": amount_cents, "category": item["category"]})
        out.append(f"{sku} x{quantity} @ {_money(unit_cents)} = {_money(amount_cents)}")

    out.append(f"Subtotal: {_money(subtotal_cents)}")

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount_cents)}")

    # All tax rules (exempt categories, discount base, rounding, rate) live in tax.py.
    tax_cents = tax.compute_tax_cents(taxable_lines, region, discount_pct)
    tax_pct = tax.tax_pct(region) if region is not None else 0
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_cents)}")

    total_cents = subtotal_cents - discount_cents + tax_cents
    out.append(f"Total: {_money(total_cents)}")

    return "\n".join(out)
