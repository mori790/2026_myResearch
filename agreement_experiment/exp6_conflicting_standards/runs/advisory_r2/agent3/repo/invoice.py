"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed team decisions:
- money_unit (float_dollars), percent_unit (fraction), lookup_miss (None)
- pricing_api: pricing.get_item(sku) -> dict|None (price float dollars, category)
               pricing.get_customer(customer_id) -> dict|None (name, discount fraction, region)
- tax.api v2:  tax.compute_tax(region, lines, discount) -> float dollars
               tax.tax_rate(region) -> float fraction or None
- tax.unknown_customer v2: region None -> tax 0.0; invoice maps an unknown customer to region None.

Money arithmetic is done in Decimal (converted from the float values at the
module boundary and rounded half up to the cent). No tax rules live here.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_decimal(value):
    """Convert a float (or int/str) dollar amount to a Decimal."""
    return Decimal(str(value))


def _round_cent(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(value):
    """Format a Decimal dollar amount as $12.50 (sign handled by caller)."""
    return "$" + format(_round_cent(value), "f")


def _percent(fraction):
    """Format a fraction as a percent with no trailing zeros: 0.10 -> '10', 0.0825 -> '8.25'."""
    pct = _to_decimal(fraction) * 100
    text = format(pct.normalize(), "f")
    return text


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_name = customer["name"]
        discount_fraction = _to_decimal(customer["discount"])
        region = customer["region"]

    out_lines = [f"Customer: {customer_name}"]

    # Build priced lines; unknown skus are reported in place and skipped.
    priced = []  # (sku, qty, unit_price Decimal, amount Decimal, category)
    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _to_decimal(item["price"])
        amount = unit_price * qty
        priced.append((sku, qty, unit_price, amount, item["category"]))
        out_lines.append(
            f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}"
        )

    subtotal = sum((p[3] for p in priced), Decimal("0"))
    discount = _round_cent(subtotal * discount_fraction)

    # Tax is computed entirely by tax.py from gross line amounts and the discount.
    tax_lines = [[category, float(amount)] for (_, _, _, amount, category) in priced]
    tax_amount = _round_cent(_to_decimal(tax.compute_tax(region, tax_lines, float(discount_fraction))))

    if region is None:
        tax_fraction = 0.0
    else:
        tax_fraction = tax.tax_rate(region)

    total = subtotal - discount + tax_amount

    out_lines.append(f"Subtotal: {_money(subtotal)}")
    out_lines.append(f"Discount ({_percent(discount_fraction)}%): -{_money(discount)}")
    out_lines.append(f"Tax ({_percent(tax_fraction)}%): {_money(tax_amount)}")
    out_lines.append(f"Total: {_money(total)}")

    return "\n".join(out_lines)
