"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed team APIs:
  pricing.get_item(sku)          -> dict {sku, name, unit_price_cents, category} or None
  pricing.get_customer(cid)      -> dict {id, name, discount_pct, region} or None
  tax.tax_breakdown(lines, region, discount_pct) -> object with
      taxable_cents, discount_pct, tax_pct, tax_cents
Money is integer cents internally and formatted as dollars only for output.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _cents_to_dollars(cents):
    """Format a non-negative integer number of cents as '$12.50'."""
    return "$%d.%02d" % (cents // 100, cents % 100)


def _percent_text(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def _round_cents(value):
    """Round a Decimal number of cents half up to whole cents, returned as int."""
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def render_invoice(order):
    """Return the invoice text for an order.

    order = {"customer": "C1", "lines": [[sku, quantity], ...]}
    """
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out = ["Customer: %s" % customer_name]
    tax_lines = []  # (category, amount_cents) for known items, before discount
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: %s" % sku)
            continue
        unit_cents = item["unit_price_cents"]
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        tax_lines.append((item["category"], amount_cents))
        out.append("%s x%d @ %s = %s" % (
            sku,
            quantity,
            _cents_to_dollars(unit_cents),
            _cents_to_dollars(amount_cents),
        ))

    # discount = subtotal * discount percent, rounded to the cent (half up).
    discount_cents = _round_cents(
        Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    )

    # Tax amount and tax percent come from tax.py.
    result = tax.tax_breakdown(tax_lines, region, discount_pct)
    tax_cents = result.tax_cents
    tax_pct = result.tax_pct

    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: %s" % _cents_to_dollars(subtotal_cents))
    out.append("Discount (%s%%): -%s" % (
        _percent_text(discount_pct), _cents_to_dollars(discount_cents)))
    out.append("Tax (%s%%): %s" % (
        _percent_text(tax_pct), _cents_to_dollars(tax_cents)))
    out.append("Total: %s" % _cents_to_dollars(total_cents))

    return "\n".join(out)
