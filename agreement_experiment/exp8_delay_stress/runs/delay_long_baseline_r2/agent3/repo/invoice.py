"""Invoice module. Owned by agent3. Implement render_invoice(order).

Data sources (agreed in the shared agreement log):
- pricing.get_item(sku)       -> dict(sku, name, price [float dollars], category) or None
- pricing.get_customer(cid)   -> dict(id, name, discount [float fraction, 0.10 = 10%], region) or None
- tax.compute_tax(lines, region, discount_pct) -> int cents
    lines: list of {"category": str, "amount_cents": int} (pre-discount line amounts)
    region: customer region, or None for unknown customer (tax is 0)
    discount_pct: percent number (10 for 10%)
- tax.tax_rate(region) -> float percent (e.g. 8.25)

This module does no tax rule computation; it only converts units and formats text.
Money is handled as decimal.Decimal in dollars internally.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_decimal(value):
    """Convert a float (or int/str) to Decimal via its string form, avoiding binary float noise."""
    return Decimal(str(value))


def _money(amount):
    """Format a Decimal dollar amount with two decimals, e.g. Decimal('12.5') -> '12.50'."""
    return f"{amount.quantize(CENT, rounding=ROUND_HALF_UP):.2f}"


def _percent_text(percent):
    """Format a percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = format(Decimal(str(percent)).normalize(), "f")
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

    discount_pct = discount_fraction * 100

    output_lines = [f"Customer: {customer_name}"]
    tax_input = []  # [{"category": ..., "amount_cents": ...}] for known items only
    subtotal = Decimal("0")

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output_lines.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = _to_decimal(item["price"])
        amount = (unit_price * quantity).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += amount
        tax_input.append({
            "category": item["category"],
            "amount_cents": int(amount * 100),
        })
        output_lines.append(
            f"{sku} x{quantity} @ ${_money(unit_price)} = ${_money(amount)}"
        )

    subtotal = subtotal.quantize(CENT, rounding=ROUND_HALF_UP)
    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_cents = tax.compute_tax(tax_input, region, float(discount_pct))
    tax_amount = (Decimal(tax_cents) / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_percent = Decimal("0") if region is None else _to_decimal(tax.tax_rate(region))

    total = subtotal - discount + tax_amount

    output_lines.append(f"Subtotal: ${_money(subtotal)}")
    output_lines.append(f"Discount ({_percent_text(discount_pct)}%): -${_money(discount)}")
    output_lines.append(f"Tax ({_percent_text(tax_percent)}%): ${_money(tax_amount)}")
    output_lines.append(f"Total: ${_money(total)}")

    return "\n".join(output_lines)
