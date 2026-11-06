"""Invoice rendering.

Uses the committed team APIs:
  pricing.get_item(sku)        -> dict | None  (price: float dollars, category)
  pricing.get_customer(id)     -> dict | None  (discount: float fraction, region)
  tax.compute_tax(region, lines, discount_pct) -> int cents
  tax.tax_percent(region)      -> float percent number

Money is handled as Decimal dollars internally; tax is integer cents at the boundary.
invoice.py does not compute any tax rule itself.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_decimal(value):
    # Convert a float from pricing/tax via str() so 7.05 becomes exactly Decimal("7.05").
    return Decimal(str(value))


def _money(value):
    """Decimal dollars -> '12.50' (no currency sign)."""
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def _percent_text(percent):
    """Percent number -> text without trailing zeros: 8.25 -> '8.25', 10 -> '10', 0 -> '0'."""
    return format(_to_decimal(percent).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (tax.py handles region None).
        customer_label = customer_id
        discount_frac = Decimal("0")
        region = None
    else:
        customer_label = customer["name"]
        discount_frac = _to_decimal(customer["discount"])
        region = customer["region"]

    item_lines = []
    taxable_lines = []  # what tax.compute_tax needs: category and pre-discount amount in cents
    subtotal = Decimal("0.00")

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            item_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = _to_decimal(item["price"])
        amount = (unit * qty).quantize(CENT, rounding=ROUND_HALF_UP)
        item_lines.append(f"{sku} x{qty} @ ${_money(unit)} = ${_money(amount)}")
        subtotal += amount
        taxable_lines.append(
            {"category": item["category"], "amount_cents": int((amount * 100).to_integral_value())}
        )

    discount = (subtotal * discount_frac).quantize(CENT, rounding=ROUND_HALF_UP)
    discount_pct = discount_frac * 100

    tax_cents = tax.compute_tax(region, taxable_lines, float(discount_pct))
    tax_amount = Decimal(tax_cents).scaleb(-2).quantize(CENT)
    tax_pct = tax.tax_percent(region)

    total = subtotal - discount + tax_amount

    out = [f"Customer: {customer_label}"]
    out.extend(item_lines)
    out.append(f"Subtotal: ${_money(subtotal)}")
    out.append(f"Discount ({_percent_text(discount_pct)}%): -${_money(discount)}")
    out.append(f"Tax ({_percent_text(tax_pct)}%): ${_money(tax_amount)}")
    out.append(f"Total: ${_money(total)}")
    return "\n".join(out)
