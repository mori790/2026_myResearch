"""Invoice module. Owned by agent3. Implement render_invoice(order).

Interfaces used (committed in the shared decision log):
  pricing.get_item(sku)          -> {"sku", "name", "price_cents", "category"} or None
  pricing.get_customer(cid)      -> {"id", "name", "discount_pct", "region"} or None
  tax.compute_tax(region, lines, discount_pct) -> int tax in cents
      lines = [(category, amount_cents), ...]; region None -> tax 0
  tax.tax_rate(region)           -> percent number; None -> 0

Money is integer cents at the module boundary (money_units). Inside this
module, amounts are Decimal dollars (team standard).
Percents are percent numbers (10 = 10%), as in money_units.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _money(amount):
    """Format a non-negative Decimal dollar amount as $12.50."""
    return "$" + format(amount.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


def _percent(value):
    """Format a percent number without trailing zeros: 10, 8.25, 0."""
    d = Decimal(str(value))
    if d == d.to_integral_value():
        return str(int(d))
    return format(d.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out = [f"Customer: {customer_name}"]
    taxable_lines = []  # (category, amount_cents) for tax.py
    subtotal = Decimal("0")

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = Decimal(item["price_cents"]) / HUNDRED
        amount = unit_price * qty
        subtotal += amount
        taxable_lines.append((item["category"], item["price_cents"] * qty))
        out.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}")

    discount = (subtotal * Decimal(str(discount_pct)) / HUNDRED).quantize(
        CENT, rounding=ROUND_HALF_UP
    )

    tax_amount = Decimal(tax.compute_tax(region, taxable_lines, discount_pct)) / HUNDRED
    tax_pct = tax.tax_rate(region)

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")

    return "\n".join(out)
