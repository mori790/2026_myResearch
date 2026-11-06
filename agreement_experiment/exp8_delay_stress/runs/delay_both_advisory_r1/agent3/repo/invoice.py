"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed decisions:
  pricing_api: pricing.get_item(sku) / pricing.get_customer(id) return dicts or None.
               Prices are float dollars; discount is a float fraction (0.10 = 10%).
  TAX_API v2:  tax.compute_tax(region, discount_pct, lines) -> int cents;
               tax.tax_percent(region) -> percent number.
Money is handled as Decimal dollars inside this module (team standard).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_decimal(value):
    # pricing and tax return floats/ints; go through str to avoid binary float error.
    return Decimal(str(value))


def _money(amount):
    """Format a non-negative Decimal dollar amount, e.g. Decimal('25') -> '$25.00'."""
    return "$" + format(amount.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def _percent_text(percent):
    """Format a Decimal percent without trailing zeros: 10 -> '10%', 8.25 -> '8.25%', 0 -> '0%'."""
    return format(percent.normalize(), "f") + "%"


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_label = customer_id
        discount_rate = Decimal("0")  # fraction, 0.10 = 10%
        region = None
    else:
        customer_label = customer["name"]
        discount_rate = _to_decimal(customer["discount"])
        region = customer["region"]

    out_lines = [f"Customer: {customer_label}"]
    subtotal = Decimal("0")
    taxable_lines = []  # passed to tax.py: pre-discount line totals in integer cents

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _to_decimal(item["price"])
        amount = unit_price * qty
        subtotal += amount
        out_lines.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}")
        taxable_lines.append({
            "category": item["category"],
            "amount_cents": int((amount * 100).to_integral_value()),
        })

    discount = (subtotal * discount_rate).quantize(CENT, rounding=ROUND_HALF_UP)
    discount_percent = discount_rate * 100

    # Tax rules live in tax.py; invoice only supplies region, discount percent and lines.
    tax_cents = tax.compute_tax(region, float(discount_percent), taxable_lines)
    tax_amount = Decimal(tax_cents) / 100
    tax_percent = _to_decimal(tax.tax_percent(region))

    total = subtotal - discount + tax_amount

    out_lines.append(f"Subtotal: {_money(subtotal)}")
    out_lines.append(f"Discount ({_percent_text(discount_percent)}): -{_money(discount)}")
    out_lines.append(f"Tax ({_percent_text(tax_percent)}): {_money(tax_amount)}")
    out_lines.append(f"Total: {_money(total)}")

    return "\n".join(out_lines)
