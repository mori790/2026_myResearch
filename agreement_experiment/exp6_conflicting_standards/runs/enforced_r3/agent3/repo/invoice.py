"""Invoice module. Owned by agent3. Implement render_invoice(order).

Calls only (committed decisions pricing_api v2 and tax_api v2):
  pricing.get_item(sku)                    -> {"sku", "name", "price" (float dollars), "category"} or None
  pricing.get_customer(cid)                -> {"id", "name", "discount" (fraction off), "region"} or None
  tax.compute_tax(region, lines, discount) -> tax in Decimal dollars
      lines = [(category, amount_dollars)] for every known item, before discount
      region None -> 0 tax
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
PROBE_AMOUNT = Decimal("10000")  # used only by the fallback in _tax_percent


def _dec(x):
    """Convert float/int/str/Decimal to Decimal via str, so 12.5 -> Decimal('12.5')."""
    return Decimal(str(x))


def _money(x):
    """Dollar amount with two decimals, no sign or symbol: 12.5 -> '12.50'."""
    return format(_dec(x).quantize(CENT, rounding=ROUND_HALF_UP), "f")


def _number(x):
    """Number without trailing zeros: 10.0 -> '10', 8.250 -> '8.25', 0 -> '0'."""
    return format(_dec(x).normalize(), "f")


def _percent_from_fraction(fraction):
    """Fraction to percent text: 0.10 -> '10', 0.0825 -> '8.25'."""
    return _number(_dec(fraction) * 100)


def _tax_percent(region):
    """Tax percent as a Decimal percent number (8.25 means 8.25%).

    Returns 0 for an unknown customer (region None) without calling tax.py.
    tax_api v2 has no tax_percent helper, so the rate is read from tax.py by
    calling compute_tax on a probe amount (10000 dollars, no discount, one
    made-up category). Result is rounded to the cent, so the percent is exact
    only to about 0.0001 percent. Assumes the made-up category is not exempt.
    """
    if region is None:
        return Decimal("0")
    probe_tax = _dec(tax.compute_tax(region, [("__probe__", PROBE_AMOUNT)], 0))
    return probe_tax * 100 / PROBE_AMOUNT


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        name = customer_id
        region = None
        discount_fraction = 0
    else:
        name = customer["name"]
        region = customer["region"]
        discount_fraction = customer["discount"]

    out = [f"Customer: {name}"]

    subtotal = Decimal("0")
    taxable_lines = []
    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _dec(item["price"])
        amount = (unit_price * qty).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += amount
        taxable_lines.append((item["category"], amount))
        out.append(f"{sku} x{qty} @ ${_money(unit_price)} = ${_money(amount)}")

    discount = (subtotal * _dec(discount_fraction)).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_amount = _dec(tax.compute_tax(region, taxable_lines, discount_fraction))
    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: ${_money(subtotal)}")
    out.append(f"Discount ({_percent_from_fraction(discount_fraction)}%): -${_money(discount)}")
    out.append(f"Tax ({_number(_tax_percent(region))}%): ${_money(tax_amount)}")
    out.append(f"Total: ${_money(total)}")

    return "\n".join(out)
