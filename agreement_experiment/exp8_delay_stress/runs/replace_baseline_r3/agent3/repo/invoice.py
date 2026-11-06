"""Invoice module. Owned by agent3. Implement render_invoice(order).

Team conventions (as agreed with agent1 and agent2):
  - pricing.get_item(sku) -> Item|None   (Item: sku, name, price float dollars, category)
  - pricing.get_customer(id) -> Customer|None
        (Customer: id, name, discount fraction e.g. 0.10, region e.g. 'TX')
  - tax.tax_details(lines, region, discount_pct) -> dict with
        taxable_cents, exempt_cents, discount_pct, tax_pct, tax_cents
    lines = [{"category": str, "amount_cents": int}], discount_pct is a percent number
    (10 means 10%). Tax rules live entirely in tax.py; this module does not compute tax.

Inside this module, money is integer cents (converted from pricing's float dollars
with Decimal, half-up), and the discount is computed here as subtotal * discount.
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(amount):
    """Convert a dollar amount (float, int, str or Decimal) to integer cents, half up."""
    cents = (Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def _money(cents):
    """Format integer cents as '12.50' (no currency sign)."""
    return f"{cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = format(Decimal(str(value)).normalize(), "f")
    return "0" if text in ("-0", "") else text


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)
    if customer is None:
        name = str(customer_id)
        region = None
        discount_pct = Decimal("0")
    else:
        name = customer.name or str(customer_id)
        region = customer.region
        discount_pct = Decimal(str(customer.discount)) * 100

    out = [f"Customer: {name}"]
    tax_lines = []  # one dict per known line, for tax.py
    subtotal_cents = 0

    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = _to_cents(item.price)
        amount_cents = unit_cents * qty
        out.append(f"{sku} x{qty} @ ${_money(unit_cents)} = ${_money(amount_cents)}")
        tax_lines.append({"category": item.category, "amount_cents": amount_cents})
        subtotal_cents += amount_cents

    # discount = subtotal * fraction, rounded to the cent (half up)
    discount_cents = int(
        (Decimal(subtotal_cents) * discount_pct / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    details = tax.tax_details(tax_lines, region, float(discount_pct))
    tax_cents = int(details["tax_cents"])
    tax_pct = details["tax_pct"]

    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append(f"Subtotal: ${_money(subtotal_cents)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -${_money(discount_cents)}")
    out.append(f"Tax ({_percent(tax_pct)}%): ${_money(tax_cents)}")
    out.append(f"Total: ${_money(total_cents)}")
    return "\n".join(out)
