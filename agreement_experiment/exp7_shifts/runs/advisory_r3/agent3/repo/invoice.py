"""Invoice module. Owned by agent3.

render_invoice(order) gets item and customer data from pricing.py
(pricing_api v1) and the tax from tax.py (tax_api v1). It does not
compute any tax rule itself.

Units (pricing_api / tax_api v1): money is float dollars, percent is a
float fraction (0.10 = 10%). Inside this module money and percents are
converted to Decimal, so the arithmetic and the cent rounding are exact.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dec(value):
    """Convert a float from pricing.py / tax.py to Decimal via its short repr."""
    return Decimal(str(value))


def _round_cent(amount):
    """Round a Decimal amount of dollars to the cent, half up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal amount of dollars as '$12.50'."""
    return "$" + str(_round_cent(amount))


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros: 0.0825 -> '8.25%', 0.10 -> '10%', 0 -> '0%'."""
    percent = (_dec(fraction) * 100).normalize()
    return format(percent, "f") + "%"


def render_invoice(order):
    """Return the invoice text for an order.

    order = {"customer": "C1", "lines": [["A", 2], ["D", 2], ["Z", 1]]}
    Lines are (sku, quantity). Unknown skus are listed as
    "UNKNOWN SKU: <sku>" and skipped in the totals.
    """
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, no discount, no tax.
        customer_label = customer_id
        discount_fraction = Decimal("0")
        tax_fraction = Decimal("0")
    else:
        customer_label = customer.get("name", customer_id)
        discount_fraction = _dec(customer.get("discount", 0))
        tax_fraction = _dec(tax.tax_rate(customer.get("region", "")))

    body = []
    subtotal = Decimal("0")
    taxable_lines = []  # passed to tax.compute_tax, amounts before discount

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            body.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = _dec(item["price"])
        amount = unit_price * quantity
        subtotal += amount
        body.append(f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}")
        taxable_lines.append({"category": item.get("category", ""), "amount": float(amount)})

    subtotal = _round_cent(subtotal)
    discount = _round_cent(subtotal * discount_fraction)
    tax_amount = _round_cent(_dec(tax.compute_tax(customer, taxable_lines)))
    total = subtotal - discount + tax_amount

    lines = [f"Customer: {customer_label}"]
    lines.extend(body)
    lines.append(f"Subtotal: {_money(subtotal)}")
    lines.append(f"Discount ({_percent(discount_fraction)}): -{_money(discount)}")
    lines.append(f"Tax ({_percent(tax_fraction)}): {_money(tax_amount)}")
    lines.append(f"Total: {_money(total)}")
    return "\n".join(lines)
