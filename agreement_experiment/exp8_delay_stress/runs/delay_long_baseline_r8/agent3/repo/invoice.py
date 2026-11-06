"""Invoice module. Owned by agent3. Implement render_invoice(order).

Depends on:
  pricing.py (agent1, pricing_api): get_item(sku), get_customer(customer_id)
  tax.py     (agent2, tax_api):     get_tax(customer_id, lines)

Money is handled as Decimal in dollars. Internally amounts are kept as integer
cents so that the discount allocation is exact.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_decimal(value):
    """Convert a float/int/str from pricing.py to Decimal without binary float noise."""
    return Decimal(str(value))


def _money(amount):
    """Format a Decimal dollar amount with two decimals, e.g. Decimal('3.9') -> '3.90'."""
    return format(amount.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


def _percent(fraction):
    """Format a Decimal fraction as a percent without trailing zeros: 0.1 -> '10', 0.0825 -> '8.25'."""
    value = (fraction * 100).normalize()
    return format(value, "f")


def _allocate_discount(line_cents, discount_cents):
    """Split discount_cents over the lines proportionally to their amounts.

    Largest-remainder method: every line gets the floor of its exact share,
    then the leftover cents go to the lines with the largest remainders
    (ties broken by line order). The shares always sum to discount_cents.
    Returns a list of integer cent amounts, one per line.
    """
    subtotal_cents = sum(line_cents)
    if subtotal_cents == 0 or discount_cents == 0:
        return [0] * len(line_cents)

    exact = [c * discount_cents for c in line_cents]  # numerator; share = exact / subtotal
    shares = [e // subtotal_cents for e in exact]
    remainders = [e % subtotal_cents for e in exact]
    leftover = discount_cents - sum(shares)

    order = sorted(range(len(line_cents)), key=lambda i: (-remainders[i], i))
    for i in order[:leftover]:
        shares[i] += 1
    return shares


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_name = customer_id
        discount_fraction = Decimal("0")
    else:
        customer_name = customer.get("name") or customer_id
        discount_fraction = _to_decimal(customer.get("discount", 0))

    # Build the lines: known items are priced, unknown skus are kept in position.
    rows = []  # each entry: ("item", sku, qty, unit_price, amount) or ("unknown", sku)
    known = []  # (sku, amount_cents) for known items, in order
    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            rows.append(("unknown", sku))
            continue
        unit_price = _to_decimal(item["price"]).quantize(CENT, rounding=ROUND_HALF_UP)
        amount = unit_price * qty
        amount_cents = int(amount / CENT)
        rows.append(("item", sku, qty, unit_price, amount))
        known.append((sku, amount_cents))

    subtotal_cents = sum(c for _, c in known)
    subtotal = Decimal(subtotal_cents) * CENT

    # discount = subtotal * discount fraction, rounded to the cent (half up)
    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)
    discount_cents = int(discount / CENT)

    # Split the invoice discount over the lines so tax.py gets net amounts
    # that add up exactly to subtotal - discount.
    alloc = _allocate_discount([c for _, c in known], discount_cents)
    net_lines = [
        (sku, Decimal(c - a) * CENT)
        for (sku, c), a in zip(known, alloc)
    ]

    tax_amount, tax_rate = tax.get_tax(customer_id, net_lines)
    tax_amount = _to_decimal(tax_amount).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_rate = _to_decimal(tax_rate)

    total = subtotal - discount + tax_amount

    out = [f"Customer: {customer_name}"]
    for row in rows:
        if row[0] == "unknown":
            out.append(f"UNKNOWN SKU: {row[1]}")
        else:
            _, sku, qty, unit_price, amount = row
            out.append(f"{sku} x{qty} @ ${_money(unit_price)} = ${_money(amount)}")

    out.append(f"Subtotal: ${_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_fraction)}%): -${_money(discount)}")
    out.append(f"Tax ({_percent(tax_rate - 1)}%): ${_money(tax_amount)}")
    out.append(f"Total: ${_money(total)}")
    return "\n".join(out)
