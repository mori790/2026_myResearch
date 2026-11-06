"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed team decisions:
  pricing_api:  pricing.get_item(sku) -> dict or None
                pricing.get_customer(customer_id) -> dict or None
  TAX_API v2:   tax.compute_tax(lines, region, discount_rate) -> (tax_dollars, tax_rate)
Boundary values are float dollars / fractions. Inside this module all money is
Decimal, rounded to the cent with ROUND_HALF_UP.
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dec(value):
    """Convert a float/int/str from pricing or tax into Decimal via its shortest repr."""
    return Decimal(str(value))


def _cents(amount):
    """Round a Decimal to the cent, half up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal as dollars with two decimals, e.g. Decimal('12.5') -> '$12.50'."""
    return "$" + f"{_cents(amount):.2f}"


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros, e.g. 0.0825 -> '8.25', 0.10 -> '10', 0 -> '0'."""
    return format((fraction * 100).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer = {"name": customer_id, "discount_rate": 0.0, "region": None}

    discount_rate = _dec(customer.get("discount_rate") or 0)
    region = customer.get("region")
    name = customer.get("name") or customer_id

    out = [f"Customer: {name}"]
    subtotal = Decimal("0")
    tax_lines = []

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _dec(item["unit_price"])
        amount = _cents(unit_price * quantity)
        subtotal += amount
        out.append(f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}")
        tax_lines.append((item.get("category", ""), float(amount)))

    discount = _cents(subtotal * discount_rate)

    tax_dollars, tax_rate = tax.compute_tax(tax_lines, region, float(discount_rate))
    tax_amount = _cents(_dec(tax_dollars))

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_rate)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(_dec(tax_rate))}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
