"""Invoice module. Owned by agent3. Implement render_invoice(order).

Depends on (agreed API, see team messages):
  pricing.get_item(sku) -> Item(sku, name, price, category) or None   (price in float dollars)
  pricing.get_customer(customer_id) -> Customer(id, name, discount, region) or None
                                       (discount is a fraction, e.g. 0.10 = 10%)
  tax.compute_tax_cents(region, discount_pct, lines) -> int cents
      region: str, or None for an unknown customer
      discount_pct: percent number (10 = 10%), 0 if none
      lines: [{'category': str, 'amount_cents': int}] for every known line, before discount
  tax.tax_rate_pct(region) -> Decimal percent (e.g. Decimal('8.25'))

This module formats the invoice only. It does not compute tax rules.
Money is computed as Decimal dollars; the tax call boundary uses integer cents.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

HUNDRED = Decimal("100")


def _cents_to_money(cents):
    """Format integer cents as dollars with two decimals, e.g. 1250 -> '$12.50'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a Decimal percent without trailing zeros, e.g. Decimal('10.00') -> '10', Decimal('8.25') -> '8.25'."""
    return format(Decimal(value).normalize(), "f")


def _round_half_up(value):
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        name = customer_id
        region = None
        discount_pct = Decimal("0")
    else:
        name = customer.name or customer_id
        region = customer.region
        discount_pct = Decimal(str(customer.discount)) * HUNDRED

    out = [f"Customer: {name}"]
    tax_lines = []  # [{'category', 'amount_cents'}] for tax.py, known skus only
    subtotal_cents = 0

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = _round_half_up(Decimal(str(item.price)) * 100)
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        tax_lines.append({"category": item.category, "amount_cents": amount_cents})
        out.append(
            f"{sku} x{qty} @ {_cents_to_money(unit_cents)} = {_cents_to_money(amount_cents)}"
        )

    discount_cents = _round_half_up(Decimal(subtotal_cents) * discount_pct / HUNDRED)
    tax_cents = tax.compute_tax_cents(region, discount_pct, tax_lines)
    tax_pct = tax.tax_rate_pct(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append(f"Subtotal: {_cents_to_money(subtotal_cents)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_cents_to_money(discount_cents)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_cents_to_money(tax_cents)}")
    out.append(f"Total: {_cents_to_money(total_cents)}")

    return "\n".join(out)
