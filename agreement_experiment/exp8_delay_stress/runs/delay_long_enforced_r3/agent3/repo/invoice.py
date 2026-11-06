"""Invoice module. Owned by agent3. Implement render_invoice(order).

Agreed APIs (agreement log topics pricing_api v2 and tax_api v2):
  pricing.get_item(sku)        -> {sku, name, price (float dollars), category} or None
  pricing.get_customer(cid)    -> {id, name, discount (fraction, 0.10 = 10%), region} or None
  tax.compute_tax(taxable_lines, region, discount_pct) -> tax in integer cents
      taxable_lines: list of (line_amount_cents, category) for all known lines
      discount_pct: percent number (10 = 10% off)
  tax.rate_percent(region)     -> tax rate as percent number (8.25), 0 for None

Money in this module is decimal.Decimal in dollars. Amounts are converted to
integer cents only at the tax.py boundary. No tax rules are computed here.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _to_money(value):
    """Convert a number (float/int/str/Decimal) to Decimal dollars rounded to the cent, half up."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _fmt_money(amount):
    """Format a non-negative Decimal as $12.50."""
    return "$" + format(_to_money(amount), ".2f")


def _fmt_percent(percent):
    """Format a percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(percent)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, with 0% discount and 0% tax.
        customer_label = customer_id
        discount_pct = Decimal("0")
        region = None
    else:
        customer_label = customer["name"]
        # pricing gives a fraction (0.10); the tax API takes a percent (10).
        discount_pct = Decimal(str(customer["discount"])) * HUNDRED
        region = customer["region"]

    out_lines = [f"Customer: {customer_label}"]

    subtotal = Decimal("0.00")
    taxable_lines = []  # (line_amount_cents, category) for known lines only

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = _to_money(item["price"])
        amount = (unit_price * qty).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += amount
        taxable_lines.append((int(amount * 100), item["category"]))

        out_lines.append(
            f"{sku} x{qty} @ {_fmt_money(unit_price)} = {_fmt_money(amount)}"
        )

    subtotal = subtotal.quantize(CENT, rounding=ROUND_HALF_UP)

    # Discount = subtotal * discount percent, rounded to the cent (half up).
    discount = (subtotal * discount_pct / HUNDRED).quantize(CENT, rounding=ROUND_HALF_UP)

    # Tax amount (integer cents from tax.py) and the displayed rate both come from tax.py.
    tax_cents = tax.compute_tax(taxable_lines, region, float(discount_pct))
    tax_amount = (Decimal(tax_cents) / HUNDRED).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_percent = tax.rate_percent(region)

    total = (subtotal - discount + tax_amount).quantize(CENT, rounding=ROUND_HALF_UP)

    out_lines.append(f"Subtotal: {_fmt_money(subtotal)}")
    out_lines.append(f"Discount ({_fmt_percent(discount_pct)}%): -{_fmt_money(discount)}")
    out_lines.append(f"Tax ({_fmt_percent(tax_percent)}%): {_fmt_money(tax_amount)}")
    out_lines.append(f"Total: {_fmt_money(total)}")

    return "\n".join(out_lines)
