"""Invoice module. Owned by agent3. Implement render_invoice(order).

Module APIs used (agreed on the shared agreement log / team messages):
  pricing.get_item(sku) -> Item | None          Item: sku, name, price (float dollars), category
  pricing.get_customer(customer_id) -> Customer | None
                                                Customer: id, name, discount (fraction, e.g. 0.10), region
  tax.compute_tax(region, discount_pct, lines) -> int cents
                                                region None = unknown customer (tax 0)
                                                discount_pct in percent numbers (10 for 10%)
                                                lines = [{"category": str, "amount_cents": int}]
  tax.tax_percent(region) -> Decimal            tax percent number (8.25 for 8.25%)

This module computes no tax rules itself.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def _money(amount):
    """Format a Decimal dollar amount as e.g. $12.50 or -$3.91."""
    amount = Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP)
    if amount < 0:
        return "-$" + format(-amount, ".2f")
    return "$" + format(amount, ".2f")


def _percent(value):
    """Format a percent number without trailing zeros (10, 8.25, 0)."""
    value = Decimal(value)
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def _dollars(price):
    """Convert a pricing float (dollars) to an exact Decimal."""
    return Decimal(str(price))


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is not None:
        name = customer.name or customer_id
        region = customer.region
        discount_pct = Decimal(str(customer.discount)) * HUNDRED
    else:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        name = customer_id
        region = None
        discount_pct = ZERO

    out = [f"Customer: {name}"]

    tax_lines = []  # pre-discount taxable-candidate lines for known skus
    subtotal = ZERO
    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = _dollars(item.price)
        amount = (unit * Decimal(qty)).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += amount
        tax_lines.append({
            "category": item.category,
            "amount_cents": int(amount * 100),
        })
        out.append(f"{sku} x{qty} @ {_money(unit)} = {_money(amount)}")

    discount = (subtotal * discount_pct / HUNDRED).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_cents = tax.compute_tax(region, discount_pct, tax_lines)
    tax_amount = (Decimal(tax_cents) / HUNDRED).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_pct = Decimal(str(tax.tax_percent(region)))

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")

    return "\n".join(out)
