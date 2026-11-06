"""Invoice module. Owned by agent3. Implement render_invoice(order).

All item, customer and tax information comes from pricing.py and tax.py.
This module only does the arithmetic on the returned values and the formatting.

Interfaces used (agreed in topic pricing_api, and agent2's tax API):
  pricing.get_item(sku)          -> dict {sku, name, price (float dollars), category} or None
  pricing.get_customer(cid)      -> dict {id, name, discount (fraction, 0.10), region} or None
  tax.calculate_tax(lines, region, discount_pct) -> int cents
      lines = [{"category": str, "amount_cents": int}], region None -> 0
  tax.tax_rate(region)           -> float percent (e.g. 8.25), None -> 0
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(value):
    """Round a Decimal to the cent, half up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _dec(value):
    """Convert a float/int from another module to Decimal via its string form."""
    return Decimal(str(value))


def _fmt_money(value):
    return "$" + format(value, ".2f")


def _fmt_percent(value):
    """Percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(value.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_name = customer["name"] or customer_id
        discount_fraction = _dec(customer["discount"])
        region = customer["region"]

    discount_pct = discount_fraction * 100

    out = [f"Customer: {customer_name}"]
    priced_lines = []   # (line text) for known skus
    tax_lines = []      # input for tax.calculate_tax
    subtotal = Decimal("0")

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = _dec(item["price"])
        amount = _money(unit_price * quantity)
        subtotal += amount

        out.append(f"{sku} x{quantity} @ {_fmt_money(_money(unit_price))} = {_fmt_money(amount)}")
        tax_lines.append({
            "category": item["category"],
            "amount_cents": int(amount * 100),
        })

    subtotal = _money(subtotal)
    discount = _money(subtotal * discount_fraction)
    tax_amount = _money(Decimal(tax.calculate_tax(tax_lines, region, float(discount_pct))) / 100)
    tax_pct = _dec(tax.tax_rate(region))
    total = _money(subtotal - discount + tax_amount)

    out.append(f"Subtotal: {_fmt_money(subtotal)}")
    out.append(f"Discount ({_fmt_percent(discount_pct)}%): -{_fmt_money(discount)}")
    out.append(f"Tax ({_fmt_percent(tax_pct)}%): {_fmt_money(tax_amount)}")
    out.append(f"Total: {_fmt_money(total)}")

    return "\n".join(out)
