"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed APIs:
  pricing_api v1: get_item(sku) -> Item|None (price in float dollars, category);
                  get_customer(id) -> Customer|None (discount as float fraction, region)
  tax_api v1:     get_tax_pct(region) -> float percent (KeyError if unknown region);
                  compute_tax(lines=[(category, amount_cents)], region, discount_pct) -> int cents
                  (region=None means unknown customer -> 0)

Team convention: money is Decimal in dollars; percents are multipliers.
Only the tax *lookup* and tax *computation* are delegated to tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(amount):
    """Format a non-negative Decimal dollar amount as e.g. $12.50."""
    return "$" + format(amount.quantize(CENT, rounding=ROUND_HALF_UP), "f")


def _pct(value):
    """Format a percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def _to_cents(dollars):
    """Convert a Decimal dollar amount to an int number of cents (half up)."""
    return int((dollars * 100).to_integral_value(rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_name = customer.name
        discount_fraction = Decimal(str(customer.discount))  # e.g. 0.10
        region = customer.region

    discount_pct = discount_fraction * 100  # e.g. 10

    out = [f"Customer: {customer_name}"]
    subtotal = Decimal("0")
    taxable_lines = []  # (category, amount_cents) passed to tax.py

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = Decimal(str(item.price))
        amount = unit_price * quantity
        subtotal += amount
        out.append(
            f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}"
        )
        taxable_lines.append((item.category, _to_cents(amount)))

    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)

    if region is None:
        tax_pct_text = "0"
        tax_amount = Decimal("0")
    else:
        tax_pct_text = _pct(tax.get_tax_pct(region))
        tax_cents = tax.compute_tax(taxable_lines, region, float(discount_pct))
        tax_amount = Decimal(tax_cents) / 100

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_pct(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({tax_pct_text}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
