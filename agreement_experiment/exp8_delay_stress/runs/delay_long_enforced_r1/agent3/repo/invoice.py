"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed APIs (agreement log: pricing_api, tax.api, tax.unknown, tax.rounding):
  pricing.get_item(sku)                        -> {sku, name, price (float dollars), category} or None
  pricing.get_customer(customer_id)            -> {id, name, discount (float fraction, 0.10 = 10%), region} or None
  tax.compute_tax(lines, region, discount_pct) -> int cents
      lines: iterable of (line_total_cents, category); discount_pct: percent number 0-100;
      region None (unknown customer) -> 0 tax
  tax.tax_rate(region)                         -> float percent (e.g. 8.25); KeyError if unknown

This module computes no tax rules itself. Floats coming from other modules are
converted with Decimal(str(x)) so that no binary-float error reaches the money math.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _dec(value):
    """Convert a float (or int/str) from another module to Decimal exactly as written."""
    return Decimal(str(value))


def _money(amount):
    """Dollar amount with exactly two decimals, e.g. '12.50'."""
    return format(amount.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def _percent(value):
    """Percent without trailing zeros: 10, 8.25, 0."""
    return format(value.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer:
        customer_label = customer["name"]
        discount_fraction = _dec(customer["discount"])
        region = customer.get("region") or None
    else:
        # Unknown customer: shown by its id, 0% discount, 0% tax.
        customer_label = customer_id
        discount_fraction = Decimal("0")
        region = None

    lines_out = [f"Customer: {customer_label}"]

    subtotal = Decimal("0")
    taxable_lines = []  # (line_total_cents, category) for known SKUs only

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if not item:
            lines_out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _dec(item["price"])
        line_total = (unit_price * quantity).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += line_total
        taxable_lines.append((int(line_total * 100), item.get("category", "")))
        lines_out.append(f"{sku} x{quantity} @ ${_money(unit_price)} = ${_money(line_total)}")

    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)
    discount_percent = discount_fraction * HUNDRED

    if region is None:
        tax_cents = tax.compute_tax(taxable_lines, None, 0)
        tax_percent = Decimal("0")
    else:
        tax_cents = tax.compute_tax(taxable_lines, region, float(discount_percent))
        tax_percent = _dec(tax.tax_rate(region))
    tax_amount = (Decimal(int(tax_cents)) / HUNDRED).quantize(CENT, rounding=ROUND_HALF_UP)

    total = subtotal - discount + tax_amount

    lines_out.append(f"Subtotal: ${_money(subtotal)}")
    lines_out.append(f"Discount ({_percent(discount_percent)}%): -${_money(discount)}")
    lines_out.append(f"Tax ({_percent(tax_percent)}%): ${_money(tax_amount)}")
    lines_out.append(f"Total: ${_money(total)}")

    return "\n".join(lines_out)
