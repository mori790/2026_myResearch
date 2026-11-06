"""Invoice module. Owned by agent3. Implement render_invoice(order).

All item, customer and tax information comes from pricing.py (agent1) and
tax.py (agent2). This module only does line arithmetic, the discount, and formatting.

APIs used:
    pricing.get_item(sku) -> Item(sku, name, price: float dollars, category) or None
    pricing.get_customer(cust_id) -> Customer(id, name, discount: float fraction, region) or None
    tax.compute_tax(lines=[{category, amount_cents}], region, discount_pct) -> int cents
        (region=None for unknown customer -> 0 tax; discount_pct is 0-100)
    tax.tax_pct(region) -> float percent (e.g. 8.25)
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_decimal(value):
    """Convert a float (or int/str) to Decimal via its string form."""
    return Decimal(str(value))


def _cents(amount):
    """Round a Decimal dollar amount to the cent, half up."""
    return Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a non-negative dollar amount as $12.50."""
    return "$" + format(_cents(amount), ".2f")


def _percent(value):
    """Format a percent such as Decimal('10') as '10' or '8.25' (no trailing zeros)."""
    return format(_to_decimal(value).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        name = customer_id
        region = None
        discount_fraction = Decimal("0")
    else:
        name = customer.name or customer_id
        region = customer.region
        discount_fraction = _to_decimal(customer.discount)

    output = ["Customer: " + name]

    tax_lines = []  # {"category", "amount_cents"} for known skus only
    subtotal = Decimal("0")
    for entry in order["lines"]:
        sku, quantity = entry[0], int(entry[1])
        item = pricing.get_item(sku)
        if item is None:
            output.append("UNKNOWN SKU: " + sku)
            continue
        unit_price = _to_decimal(item.price)
        line_amount = _cents(unit_price * quantity)
        subtotal += line_amount
        tax_lines.append({
            "category": item.category,
            "amount_cents": int(line_amount * 100),
        })
        output.append(
            "{} x{} @ {} = {}".format(sku, quantity, _money(unit_price), _money(line_amount))
        )

    subtotal = _cents(subtotal)

    discount_pct = discount_fraction * 100
    discount = _cents(subtotal * discount_fraction)

    tax_cents = int(tax.compute_tax(
        lines=tax_lines,
        region=region,
        discount_pct=float(discount_pct),
    ))
    tax_amount = _cents(Decimal(tax_cents) / 100)
    tax_rate = Decimal("0") if region is None else _to_decimal(tax.tax_pct(region))

    total = _cents(subtotal - discount + tax_amount)

    output.append("Subtotal: " + _money(subtotal))
    output.append("Discount ({}%): -{}".format(_percent(discount_pct), _money(discount)))
    output.append("Tax ({}%): {}".format(_percent(tax_rate), _money(tax_amount)))
    output.append("Total: " + _money(total))

    return "\n".join(output)
