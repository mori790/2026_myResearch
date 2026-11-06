"""Invoice module. Owned by agent3. Implement render_invoice(order).

Item and customer data come from pricing.py; tax amounts and tax rates come
from tax.py. This module does not apply any tax rule itself.

Agreed APIs (see agreement topic 'tax_api' and the pricing API published by agent1):
  pricing.get_item(sku)       -> Item | None      (Item: sku, name, price (float dollars), category)
  pricing.get_customer(cid)   -> Customer | None  (Customer: id, name, discount (fraction, 0.10), region)
  tax.compute_tax(lines, region, discount_pct=0) -> int cents
      lines = [{"category": str, "amount_cents": int}], region None = unknown customer
  tax.get_rate(region)        -> Decimal percent (e.g. 8.25)
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dec(value):
    """Convert a dollar amount (float, int, str or Decimal) to Decimal exactly."""
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _money(amount):
    """Format a Decimal dollar amount with 2 decimals, e.g. 12.5 -> '$12.50'."""
    return "$" + format(amount.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def _percent(value):
    """Format a Decimal percent without trailing zeros: 10.00 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(_dec(value).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None).
        display_name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        display_name = customer.name
        discount_fraction = _dec(customer.discount)
        region = customer.region

    out = [f"Customer: {display_name}"]
    subtotal = Decimal("0")
    taxable_lines = []

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _dec(item.price)
        amount = unit_price * quantity
        subtotal += amount
        out.append(f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}")
        taxable_lines.append({
            "category": item.category,
            "amount_cents": int((amount * 100).to_integral_value()),
        })

    discount_pct = discount_fraction * 100
    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_cents = tax.compute_tax(taxable_lines, region, discount_pct)
    tax_amount = Decimal(tax_cents) / 100
    tax_pct = Decimal("0") if region is None else _dec(tax.get_rate(region))

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
