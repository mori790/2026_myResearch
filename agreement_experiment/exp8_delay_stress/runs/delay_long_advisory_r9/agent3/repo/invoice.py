"""Invoice module. Owned by agent3. Implement render_invoice(order).

Follows the committed team decisions:
  pricing_api            get_item(sku) -> dict | None   (unit_price float dollars, category)
                         get_customer(cid) -> dict | None (name, discount_rate fraction, region)
  tax_api (v2)           tax.compute_tax(region, discount_rate, lines)
                         -> {"tax_rate": fraction, "taxable_base": float, "tax": float dollars}
  tax_unknown_region     region None (unknown customer) -> 0% tax

Invoice never computes tax rules itself. Money is handled as Decimal inside
this module (converted from the float dollars that pricing/tax return).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(value):
    """Convert float dollars (or a number) to a Decimal rounded half-up to the cent."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _percent_text(fraction):
    """Show a fraction as a percent without trailing zeros: 0.1 -> '10', 0.0825 -> '8.25', 0 -> '0'."""
    pct = Decimal(str(fraction)) * 100
    return format(pct.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, and region None -> 0% tax (tax_unknown_region).
        name = customer_id
        discount_rate = 0.0
        region = None
    else:
        name = customer["name"]
        discount_rate = customer["discount_rate"]
        region = customer["region"]

    out_lines = []
    subtotal = Decimal("0")
    taxable_lines = []  # passed to tax.compute_tax; amounts are before discount

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _money(item["unit_price"])
        amount = unit_price * qty
        subtotal += amount
        out_lines.append(f"{sku} x{qty} @ ${unit_price:.2f} = ${amount:.2f}")
        taxable_lines.append({"category": item["category"], "amount": float(amount)})

    discount = (subtotal * Decimal(str(discount_rate))).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_info = tax.compute_tax(region, discount_rate, taxable_lines)
    tax_rate = tax_info["tax_rate"]
    tax_amount = _money(tax_info["tax"])

    total = subtotal - discount + tax_amount

    lines = [f"Customer: {name}"]
    lines.extend(out_lines)
    lines.append(f"Subtotal: ${subtotal:.2f}")
    lines.append(f"Discount ({_percent_text(discount_rate)}%): -${discount:.2f}")
    lines.append(f"Tax ({_percent_text(tax_rate)}%): ${tax_amount:.2f}")
    lines.append(f"Total: ${total:.2f}")
    return "\n".join(lines)
