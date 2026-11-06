"""Invoice module. Owned by agent3. Implement render_invoice(order).

Item and customer data come from pricing.py (agent1); sales tax comes from
tax.py (agent2). This module does no tax computation itself.

Team convention: money is decimal.Decimal in dollars. pricing.py and tax.py
use dollars as float and cents as int respectively, so values are converted
at this boundary only.
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_dollars(value):
    """Convert a float/int/str price from pricing.py to a Decimal."""
    return Decimal(str(value))


def _money(amount):
    """Format a Decimal dollar amount as '$12.50' (rounded half up to the cent)."""
    q = amount.quantize(CENT, rounding=ROUND_HALF_UP)
    sign = "-" if q < 0 else ""
    return f"{sign}${abs(q):.2f}"


def _percent_text(percent):
    """Format a percent Decimal without trailing zeros: 10, 8.25, 0."""
    return format(percent.normalize(), "f")


def render_invoice(order):
    """Return the invoice text for an order.

    order: {"customer": <customer id str>, "lines": [[sku, quantity], ...]}
    """
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_label = customer_id
        discount_fraction = Decimal("0")
        tax_customer = None  # tax.py: unknown customer -> 0% tax, no discount
    else:
        customer_label = customer.name
        discount_fraction = _to_dollars(customer.discount)  # e.g. 0.10
        tax_customer = {
            "region": customer.region,
            "discount_pct": float(discount_fraction * 100),  # tax_api uses percent
        }

    out = [f"Customer: {customer_label}"]
    subtotal = Decimal("0")
    tax_lines = []

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _to_dollars(item.price)
        amount = (unit_price * quantity).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += amount
        out.append(
            f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}"
        )
        tax_lines.append({
            "category": item.category,
            "amount_cents": int(amount * 100),
        })

    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)
    discount_percent = _percent_text(discount_fraction * 100)

    tax_result = tax.calculate_tax(tax_lines, tax_customer)
    tax_amount = Decimal(tax_result["tax_cents"]) / Decimal(100)
    tax_percent = _percent_text(Decimal(str(tax_result["tax_pct"])))

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({discount_percent}%): -{_money(discount)}")
    out.append(f"Tax ({tax_percent}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
