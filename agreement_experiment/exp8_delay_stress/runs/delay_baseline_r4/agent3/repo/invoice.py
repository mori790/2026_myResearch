"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the agreed APIs (agreement topics pricing_api and tax_api):
  pricing.get_item(sku)          -> dict {sku, name, price (float dollars), category} or None
  pricing.get_customer(cid)      -> dict {id, name, discount_rate (fraction), region} or None
  tax.get_tax_pct(region)        -> float percent (8.25 = 8.25%); 0 when region is None
  tax.compute_tax(lines, region, discount_pct) -> int cents
      lines = [{"category": str, "amount_cents": int}], discount_pct = percent number (10 = 10%)

Money inside this module is decimal.Decimal in dollars; percentages are shown
as percent numbers. Tax rules are NOT computed here: tax.py decides the tax.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(amount):
    """Format a Decimal dollar amount as $12.50."""
    return "$" + format(amount, ".2f")


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def _to_cents(amount):
    """Convert a Decimal dollar amount to an integer number of cents."""
    return int(amount.quantize(CENT, rounding=ROUND_HALF_UP) * 100)


def render_invoice(order):
    """Return the invoice text for an order such as
    {"customer": "C1", "lines": [["A", 2], ["D", 2], ["Z", 1]]}.
    Lines are joined with "\\n" and there is no trailing newline.
    """
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None).
        name = customer_id
        discount_rate = Decimal("0")
        region = None
    else:
        name = customer["name"]
        discount_rate = Decimal(str(customer["discount_rate"]))
        region = customer["region"]

    out = [f"Customer: {name}"]
    subtotal = Decimal("0.00")
    tax_lines = []

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = Decimal(str(item["price"]))
        amount = (unit_price * qty).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += amount
        out.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}")
        tax_lines.append({"category": item["category"], "amount_cents": _to_cents(amount)})

    discount = (subtotal * discount_rate).quantize(CENT, rounding=ROUND_HALF_UP)
    discount_pct = discount_rate * 100

    # tax.py applies its own taxable base and exemptions; the tax is returned in cents.
    tax_cents = tax.compute_tax(tax_lines, region, float(discount_pct))
    tax_amount = (Decimal(tax_cents) / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_pct = tax.get_tax_pct(region)

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
