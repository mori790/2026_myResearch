"""Invoice module. Owned by agent3. Implement render_invoice(order).

Contracts used (committed in the agreement log):
  pricing.get_item(sku)        -> {"sku", "name", "unit_price" (float dollars), "category"} or None
  pricing.get_customer(id)     -> {"id", "name", "discount_rate" (fraction), "region"} or None
  tax.compute_tax(lines, region, discount_rate=0) -> TaxResult
      lines = [(category, amount_dollars)] before discount, region None = unknown customer
      TaxResult.tax  = tax amount in dollars (rounded half up to the cent)
      TaxResult.rate = tax rate as a fraction (0.0825 for 8.25%)

This module computes no tax rules itself. Money from other modules is converted
to Decimal via str() so float binary noise does not leak into the totals.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dec(value):
    """Convert a float, int or str from another module to Decimal."""
    return Decimal(str(value))


def _cents(value):
    """Round a Decimal amount to the cent, half up."""
    return _dec(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _money(value):
    """Format a non-negative dollar amount, e.g. Decimal('12.5') -> '$12.50'."""
    return "$" + format(_cents(value), ".2f")


def _pct(fraction):
    """Format a fraction as a percent without trailing zeros.

    0.0825 -> "8.25", 0.10 -> "10", 0 -> "0".
    """
    return format((_dec(fraction) * 100).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None).
        customer_name = customer_id
        discount_rate = Decimal("0")
        region = None
    else:
        customer_name = customer["name"] or customer_id
        discount_rate = _dec(customer["discount_rate"])
        region = customer["region"]

    out = ["Customer: " + customer_name]
    tax_lines = []  # (category, amount_dollars) for known SKUs, before discount
    subtotal = Decimal("0")

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: " + str(sku))
            continue
        unit_price = _dec(item["unit_price"])
        amount = _cents(unit_price * quantity)
        out.append(
            f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}"
        )
        subtotal += amount
        tax_lines.append((item["category"], float(amount)))

    discount = _cents(subtotal * discount_rate)
    result = tax.compute_tax(tax_lines, region, float(discount_rate))
    tax_amount = _cents(result.tax)
    tax_pct = _pct(result.rate)
    total = subtotal - discount + tax_amount

    out.append("Subtotal: " + _money(subtotal))
    out.append(f"Discount ({_pct(discount_rate)}%): -{_money(discount)}")
    out.append(f"Tax ({tax_pct}%): {_money(tax_amount)}")
    out.append("Total: " + _money(total))
    return "\n".join(out)
