"""Invoice module. Owned by agent3. Implement render_invoice(order).

Interfaces used (committed decisions pricing_api and tax_api_v2):
  pricing.get_item(sku)            -> dict {sku, name, price (float dollars), category} or None
  pricing.get_customer(cid)        -> dict {id, name, discount (float fraction), region} or None
  tax.tax_rate(region)             -> float fraction (0.0825 for 8.25%); 0.0 when region is None
  tax.tax_amount(region, lines, discount)
                                   -> float dollars, rounded half up to the cent;
                                      lines = [(category, amount_float_dollars)] before discount

Money is handled as decimal.Decimal dollars internally (team standard). Floats from
pricing/tax are converted with Decimal(str(x)) so their decimal representation is kept.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dec(x):
    """Convert a float (or int/str) from pricing/tax to Decimal without binary float error."""
    return Decimal(str(x))


def _money(d):
    """Format a Decimal dollar amount with exactly two decimals (no sign handling)."""
    return format(d.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros: 0.1 -> '10', 0.0825 -> '8.25', 0 -> '0'."""
    pct = _dec(fraction) * 100
    return format(pct.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_label = customer_id
        discount_fraction = 0.0
        region = None
    else:
        customer_label = customer["name"]
        discount_fraction = customer["discount"]
        region = customer["region"]

    out_lines = [f"Customer: {customer_label}"]

    subtotal = Decimal("0")
    taxable_lines = []  # (category, amount as float dollars), before discount

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = _dec(item["price"])
        amount = unit * qty
        subtotal += amount
        out_lines.append(f"{sku} x{qty} @ ${_money(unit)} = ${_money(amount)}")
        taxable_lines.append((item["category"], float(amount)))

    discount_rate = _dec(discount_fraction)
    discount = (subtotal * discount_rate).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_amount = _dec(tax.tax_amount(region, taxable_lines, discount_fraction))
    tax_amount = tax_amount.quantize(CENT, rounding=ROUND_HALF_UP)
    tax_rate = tax.tax_rate(region)

    total = subtotal - discount + tax_amount

    out_lines.append(f"Subtotal: ${_money(subtotal)}")
    out_lines.append(f"Discount ({_percent(discount_fraction)}%): -${_money(discount)}")
    out_lines.append(f"Tax ({_percent(tax_rate)}%): ${_money(tax_amount)}")
    out_lines.append(f"Total: ${_money(total)}")

    return "\n".join(out_lines)
