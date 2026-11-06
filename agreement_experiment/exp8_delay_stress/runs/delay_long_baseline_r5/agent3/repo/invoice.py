"""Invoice module. Owned by agent3. Implement render_invoice(order).

Team conventions used here:
  - Money inside this module is decimal.Decimal in dollars.
  - pricing.py (agent1) returns float dollars and discount fractions (0.10 = 10%);
    they are converted to Decimal at this module's boundary.
  - tax.py (agent2) takes integer cents and returns a Decimal percent / int cents;
    conversion happens here too.
  - Percents are shown without trailing zeros (10%, 8.25%, 0%).
  - Tax rules are NOT computed here; tax.py does that.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dollars(value):
    """Convert a float/int/str dollar value to a Decimal rounded to the cent."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a non-negative Decimal dollar amount as '$12.50'."""
    return "${:.2f}".format(amount.quantize(CENT, rounding=ROUND_HALF_UP))


def _percent(value):
    """Format a percent number without trailing zeros: 10, 8.25, 0."""
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        region = None
        discount_fraction = Decimal("0")
    else:
        customer_name = customer.name
        region = customer.region
        discount_fraction = Decimal(str(customer.discount))

    # Discount percent as a number, e.g. Decimal('10') for 10%.
    discount_pct = discount_fraction * 100

    out_lines = ["Customer: {}".format(customer_name)]

    subtotal = Decimal("0")
    taxable_lines = []  # (category, amount_cents) for tax.compute_tax

    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: {}".format(sku))
            continue

        unit_price = _dollars(item.price)
        line_amount = unit_price * qty
        subtotal += line_amount
        taxable_lines.append((item.category, int(line_amount * 100)))

        out_lines.append("{} x{} @ {} = {}".format(
            sku,
            qty,
            _money(unit_price),
            _money(line_amount),
        ))

    # Discount = subtotal * discount percent, rounded to the cent (half up).
    discount = (subtotal * discount_pct / 100).quantize(
        CENT, rounding=ROUND_HALF_UP)

    # Tax amount (int cents) and rate (percent) come from tax.py.
    tax_cents = tax.compute_tax(taxable_lines, region,
                                discount_pct=float(discount_pct))
    tax_amount = Decimal(tax_cents) / 100
    tax_rate = tax.tax_rate_pct(region)

    total = subtotal - discount + tax_amount

    out_lines.append("Subtotal: {}".format(_money(subtotal)))
    out_lines.append("Discount ({}%): -{}".format(
        _percent(discount_pct), _money(discount)))
    out_lines.append("Tax ({}%): {}".format(
        _percent(tax_rate), _money(tax_amount)))
    out_lines.append("Total: {}".format(_money(total)))

    return "\n".join(out_lines)
