"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed APIs:
  pricing_api v1: get_item(sku) -> Item|None, get_customer(id) -> Customer|None
                  (Item.price is float dollars, Customer.discount is a fraction, 0.10 = 10%)
  tax_api v1:     compute_tax(lines, customer) -> int cents,
                  lines = [(category, amount_cents)], customer None -> 0
                  get_rate(region) -> float percent (8.25 = 8.25%)

Money is Decimal in dollars (team standard). This module computes no tax rules itself.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ZERO = Decimal("0")


def _dec(value):
    """Convert a float/int/str to Decimal via its string form (avoids binary float noise)."""
    return Decimal(str(value))


def _quantize(value):
    """Round a dollar amount to the cent, half up."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(value):
    """Format a dollar amount as '$12.50'."""
    return "$" + str(_quantize(value))


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(_dec(value).normalize(), "f")


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    out = [f"Customer: {customer.name if customer is not None else customer_id}"]

    subtotal = ZERO
    taxable_lines = []  # (category, amount_cents) for tax.compute_tax
    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = _quantize(_dec(item.price))
        amount = _quantize(unit * qty)
        subtotal += amount
        out.append(f"{sku} x{qty} @ {_money(unit)} = {_money(amount)}")
        unit_cents = int(_dec(item.price).scaleb(2).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        taxable_lines.append((item.category, unit_cents * qty))

    if customer is not None:
        discount_fraction = _dec(customer.discount)
        tax_percent = _dec(tax.get_rate(customer.region))
    else:
        discount_fraction = ZERO
        tax_percent = ZERO

    discount = _quantize(subtotal * discount_fraction)
    tax_amount = _quantize(Decimal(tax.compute_tax(taxable_lines, customer)) / 100)
    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_fraction * 100)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_percent)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")

    return "\n".join(out)
