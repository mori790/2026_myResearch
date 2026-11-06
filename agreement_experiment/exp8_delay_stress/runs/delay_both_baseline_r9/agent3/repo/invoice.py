"""Invoice module. Owned by agent3. Implement render_invoice(order).

Dependencies (APIs as implemented by agent1 and agent2):
  pricing.get_customer(customer_id) -> {'id','name','discount','region'} or None
      discount: fraction (0.10 = 10% off)
  pricing.get_item(sku) -> {'sku','name','price','category'} or None
      price: float dollars
  tax.compute_tax(region, lines, discount_pct) -> int cents
      region None = unknown customer -> 0 tax
      lines: list of (category, line_amount_cents), before discount, known items only
      discount_pct: customer discount in percent (e.g. 10)
  tax.get_tax_pct(region) -> Decimal percent (e.g. 8.25); None -> 0

This module does no tax rule computation itself. Money is converted to
Decimal dollars internally; the boundary with the other modules is cents/percent.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(amount):
    """Format a Decimal dollar amount with 2 decimals, rounding half up."""
    return "$" + format(amount.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def _percent(value):
    """Format a percent Decimal without trailing zeros (10, 8.25, 0)."""
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]

    # Unknown customer: shown by id, 0% discount, 0% tax (region None).
    customer = pricing.get_customer(customer_id)
    if customer is None:
        name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        name = customer["name"]
        discount_fraction = Decimal(str(customer["discount"]))
        region = customer["region"]

    discount_pct = discount_fraction * 100

    lines_out = [f"Customer: {name}"]
    subtotal_cents = 0
    taxable_lines = []  # (category, line amount in cents before discount) for tax.py

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            lines_out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = Decimal(str(item["price"]))
        line_amount = unit_price * quantity
        line_cents = int((line_amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        subtotal_cents += line_cents
        taxable_lines.append((item["category"], line_cents))
        lines_out.append(f"{sku} x{quantity} @ {_money(unit_price)} = {_money(line_amount)}")

    subtotal = Decimal(subtotal_cents) / 100
    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_cents = tax.compute_tax(region, taxable_lines, discount_pct)
    tax_amount = Decimal(tax_cents) / 100
    tax_pct = Decimal(str(tax.get_tax_pct(region) or 0))

    total = subtotal - discount + tax_amount

    lines_out.append(f"Subtotal: {_money(subtotal)}")
    lines_out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    lines_out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_amount)}")
    lines_out.append(f"Total: {_money(total)}")

    return "\n".join(lines_out)
