"""Invoice module. Owned by agent3. Implements render_invoice(order).

Interfaces used (committed in agreement log):
  pricing.get_item(sku)          -> dict {sku, name, price (float dollars), category} or None
  pricing.get_customer(cust_id)  -> dict {id, name, discount (float fraction), region (str)} or None
  tax.compute_tax(lines, region, discount) -> float dollars
      lines = [(category, amount_dollars), ...], region None for unknown customer, discount fraction
  tax.rate_pct(region) -> str, nominal percent such as "8.25", "0" for region None

Money is handled as decimal.Decimal dollars internally; float values from the other
modules are converted with Decimal(str(x)).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ZERO = Decimal("0")


def _to_decimal(value):
    """Convert a float (or int/str) from another module to an exact Decimal."""
    return Decimal(str(value))


def _money(amount):
    """Format a non-negative Decimal dollar amount as $12.50 (rounded half up)."""
    return "$" + format(amount.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def _percent(value):
    """Format a percent without trailing zeros: 10, 8.25, 0."""
    return format(_to_decimal(value).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by its id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_frac = ZERO
        region = None
    else:
        customer_name = customer["name"]
        discount_frac = _to_decimal(customer["discount"])  # fraction, 0.10 = 10%
        region = customer["region"]

    out_lines = []
    tax_lines = []  # (category, amount in dollars) for known items only
    subtotal = ZERO

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _to_decimal(item["price"])
        amount = unit_price * qty
        subtotal += amount
        out_lines.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}")
        tax_lines.append((item["category"], float(amount)))

    discount = (subtotal * discount_frac).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_amount = _to_decimal(
        tax.compute_tax(tax_lines, region, float(discount_frac))
    ).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_pct = tax.rate_pct(region)

    total = subtotal - discount + tax_amount

    out = [f"Customer: {customer_name}"]
    out.extend(out_lines)
    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_frac * 100)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
