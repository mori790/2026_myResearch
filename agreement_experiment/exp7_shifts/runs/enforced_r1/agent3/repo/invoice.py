"""Invoice module. Owned by agent3. Implement render_invoice(order).

Units (per committed decisions pricing_api v1 and tax_api v1):
  - pricing.py: money as float dollars, discount as fraction (0.10 = 10%).
  - tax.py:     money as int cents, percent as percent number (10 = 10%).
This module converts at the boundary and uses Decimal dollars internally.
Tax rules (exemptions, base, rounding) are NOT implemented here; they come from tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _money(amount):
    """Format a non-negative Decimal dollar amount as '$12.50'."""
    return "$" + format(amount.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


def _pct(value):
    """Format a percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = format(Decimal(str(value)), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _to_cents(amount):
    """Convert a Decimal dollar amount to int cents, rounding half up."""
    return int((amount * HUNDRED).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    """Return the invoice text for an order {"customer": id, "lines": [[sku, qty], ...]}."""
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        name = customer.name
        discount_fraction = Decimal(str(customer.discount))
        region = customer.region

    output = [f"Customer: {name}"]
    subtotal = Decimal("0")
    taxable_lines = []

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = Decimal(str(item.price))
        amount = (unit_price * quantity).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += amount
        output.append(f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}")
        # Only non-exempt lines are passed to tax.py; exemption is decided by tax.py.
        if not tax.is_exempt(item.category):
            taxable_lines.append(tax.TaxLine(item.category, _to_cents(amount)))

    discount_pct = discount_fraction * HUNDRED  # percent number, e.g. 10
    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)

    if region is None:
        tax_pct = Decimal("0")
    else:
        tax_pct = Decimal(str(tax.get_tax_pct(region)))
    # tax.py applies the discount to the taxable base itself (see tax_api v1).
    tax_cents = tax.compute_tax(taxable_lines, region, discount_pct=float(discount_pct))
    tax_amount = Decimal(tax_cents) / HUNDRED

    total = subtotal - discount + tax_amount

    output.append(f"Subtotal: {_money(subtotal)}")
    output.append(f"Discount ({_pct(discount_pct)}%): -{_money(discount)}")
    output.append(f"Tax ({_pct(tax_pct)}%): {_money(tax_amount)}")
    output.append(f"Total: {_money(total)}")
    return "\n".join(output)
