"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed APIs (PRICING_API and tax_api):
  pricing.get_item(sku)                        -> {"sku","name","price"(float $),"category"} or None
  pricing.get_customer(customer_id)            -> {"id","name","discount"(fraction),"region"} or None
  tax.compute_tax(region, lines, discount_pct) -> tax in integer cents
      lines = [(category, amount_cents)], discount_pct in percent numbers
  tax.tax_rate(region)                         -> percent number (None -> 0)

Internal convention: money is decimal.Decimal dollars. Converting at the
boundary: pricing float dollars -> Decimal, tax integer cents -> Decimal dollars.
No tax rules are computed here.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(value):
    """Convert a float/int/str dollar amount into a Decimal rounded to the cent."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _fmt_money(amount):
    """Format a non-negative Decimal dollar amount as e.g. $12.50."""
    return "${:.2f}".format(amount)


def _fmt_percent(percent):
    """Format a percent number without trailing zeros: 10, 8.25, 0."""
    return format(Decimal(str(percent)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (tax.py handles region None).
        name = customer_id
        discount_frac = Decimal("0")
        region = None
    else:
        name = customer.get("name", customer_id)
        discount_frac = Decimal(str(customer.get("discount", 0)))
        region = customer.get("region")

    out_lines = [f"Customer: {name}"]
    subtotal = Decimal("0")
    taxable_lines = []  # (category, amount_cents) for known skus only

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _money(item["price"])
        amount = (unit_price * quantity).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += amount
        out_lines.append(f"{sku} x{quantity} @ {_fmt_money(unit_price)} = {_fmt_money(amount)}")
        taxable_lines.append((item.get("category", ""), int(amount * 100)))

    discount_percent = discount_frac * 100
    discount = (subtotal * discount_frac).quantize(CENT, rounding=ROUND_HALF_UP)

    # Tax amount (cents) and displayed rate (percent number) come from tax.py.
    tax_cents = tax.compute_tax(region, taxable_lines, float(discount_percent))
    tax_amount = Decimal(tax_cents) / 100
    tax_percent = Decimal(str(tax.tax_rate(region)))

    total = subtotal - discount + tax_amount

    out_lines.append(f"Subtotal: {_fmt_money(subtotal)}")
    out_lines.append(f"Discount ({_fmt_percent(discount_percent)}%): -{_fmt_money(discount)}")
    out_lines.append(f"Tax ({_fmt_percent(tax_percent)}%): {_fmt_money(tax_amount)}")
    out_lines.append(f"Total: {_fmt_money(total)}")

    return "\n".join(out_lines)
