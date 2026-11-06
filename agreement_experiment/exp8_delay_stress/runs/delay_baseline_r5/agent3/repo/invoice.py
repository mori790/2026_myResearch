"""Invoice module. Owned by agent3. Implement render_invoice(order).

All item, customer and tax information comes from pricing.py and tax.py.
This module only does arithmetic on money and formatting. It does not
compute tax rules itself.

Agreed interfaces (agreement topics pricing_api and tax_api):
  pricing.get_item(sku)          -> dict {sku, name, price (float dollars), category} or None
  pricing.get_customer(cid)      -> dict {id, name, discount (fraction, 0.10 = 10%), region} or None
  tax.compute_tax(lines, region, discount_pct) -> int cents
        lines: iterable of (category, amount_cents) for all known order lines
        region: None for an unknown customer (tax is 0)
        discount_pct: percent number (10 means 10%)
  tax.tax_rate_pct(region)       -> Decimal percent (None -> 0)

Money inside this module is decimal.Decimal in dollars. Conversion from
the float/cents/fraction conventions of the other modules happens only at
the boundary in this file.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


CENT = Decimal("0.01")
ZERO = Decimal("0")
HUNDRED = Decimal("100")


def _money(amount):
    """Format a Decimal dollar amount with two decimals, e.g. Decimal('12.5') -> '$12.50'."""
    return "${:.2f}".format(amount)


def _percent(value):
    """Format a percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0.00 -> '0'."""
    value = Decimal(value)
    text = format(value.normalize(), "f")
    return text


def _to_decimal(value):
    """Convert a float/int/str from another module to Decimal via str() to avoid binary float noise."""
    return Decimal(str(value))


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_label = customer_id
        discount_frac = ZERO
        region = None
    else:
        customer_label = customer.get("name") or customer_id
        discount_frac = _to_decimal(customer.get("discount", 0))
        region = customer.get("region")

    output_lines = ["Customer: {}".format(customer_label)]

    subtotal = ZERO
    taxable_lines = []  # (category, amount_cents) for known skus only

    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            output_lines.append("UNKNOWN SKU: {}".format(sku))
            continue

        unit_price = _to_decimal(item["price"])
        quantity = _to_decimal(qty)
        amount = (unit_price * quantity).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += amount

        output_lines.append("{} x{} @ {} = {}".format(
            sku, qty, _money(unit_price), _money(amount)))

        amount_cents = int(amount * HUNDRED)
        taxable_lines.append((item.get("category", ""), amount_cents))

    discount_pct = discount_frac * HUNDRED
    discount = (subtotal * discount_frac).quantize(CENT, rounding=ROUND_HALF_UP)

    # tax_api takes a plain number for the percent; pass float, not Decimal.
    tax_cents = tax.compute_tax(taxable_lines, region, float(discount_pct))
    tax_amount = Decimal(tax_cents) / HUNDRED
    tax_pct = Decimal(tax.tax_rate_pct(region) or ZERO)

    total = subtotal - discount + tax_amount

    output_lines.append("Subtotal: {}".format(_money(subtotal)))
    output_lines.append("Discount ({}%): -{}".format(_percent(discount_pct), _money(discount)))
    output_lines.append("Tax ({}%): {}".format(_percent(tax_pct), _money(tax_amount)))
    output_lines.append("Total: {}".format(_money(total)))

    return "\n".join(output_lines)
