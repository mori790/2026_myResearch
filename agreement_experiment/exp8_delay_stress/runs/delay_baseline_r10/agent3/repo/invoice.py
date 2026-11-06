"""Invoice module. Owned by agent3. Implement render_invoice(order).

Contracts used (agreed with teammates):
  pricing.get_item(sku)          -> Item | None   (Item: sku, name, price [dollars], category)
  pricing.get_customer(cust_id)  -> Customer | None (Customer: id, name, discount [fraction], region)
  tax.compute_tax(lines, region, discount_pct) -> int cents
      lines = [(category, amount_cents), ...] for known items, before discount
      discount_pct = percent number (10 for 10%)
  tax.tax_pct(region) -> float percent (None -> 0)

Team convention inside this module: money is Decimal dollars.
Conversion to/from integer cents happens only at the compute_tax boundary.
No tax rules are implemented here.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_decimal(value):
    """Convert a float/str/int from pricing into an exact Decimal."""
    return Decimal(str(value))


def _money(amount):
    """Format a Decimal dollar amount as '$12.50' (no sign)."""
    return "$" + format(amount.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def _pct(percent):
    """Format a Decimal percent without trailing zeros, e.g. 10, 8.25, 0."""
    return format(percent.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        customer_name = customer_id
        region = None
        discount_rate = Decimal("0")
    else:
        customer_name = customer.name
        region = customer.region
        discount_rate = _to_decimal(customer.discount)  # fraction, 0.10 = 10%

    discount_percent = discount_rate * 100  # Decimal percent, e.g. Decimal('10.0')

    out = [f"Customer: {customer_name}"]
    subtotal = Decimal("0.00")
    taxable_lines = []  # (category, amount_cents) for known items, before discount

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _to_decimal(item.price).quantize(CENT, rounding=ROUND_HALF_UP)
        amount = unit_price * qty
        subtotal += amount
        out.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}")
        taxable_lines.append((item.category, int(amount * 100)))

    discount = (subtotal * discount_rate).quantize(CENT, rounding=ROUND_HALF_UP)

    # Tax is computed by tax.py only (returns int cents).
    tax_cents = tax.compute_tax(taxable_lines, region, float(discount_percent))
    tax_amount = Decimal(tax_cents) / Decimal(100)
    tax_rate = _to_decimal(tax.tax_pct(region))  # percent number, e.g. 8.25

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_pct(discount_percent)}%): -{_money(discount)}")
    out.append(f"Tax ({_pct(tax_rate)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
