"""Invoice module. Owned by agent3.

render_invoice(order) builds the text of an invoice. It gets item and customer
data from pricing.py and all tax data from tax.py; it computes no tax rules.

Units follow the committed decisions in the agreement log:
  money_units v1   : money is integer cents (1250 = $12.50); percents are numbers (8.25 = 8.25%).
  pricing_api v2   : pricing.get_item / get_customer / get_unit_price_cents / get_discount_pct
                     return None on a miss.
  tax_interface v2 : tax.compute_tax(region, discount_pct, lines) -> int cents;
                     tax.rate_pct(region) -> percent number, used for display.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _round_half_up(value):
    """Round a Decimal to a whole number, halves going up, and return an int."""
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format non-negative integer cents as '$12.50'."""
    dollars, rem = divmod(int(cents), 100)
    return "${}.{:02d}".format(dollars, rem)


def _signed_money(cents):
    """Format a deduction as '-$3.91' (always with a minus sign)."""
    return "-" + _money(cents)


def _percent(value):
    """Format a percent without trailing zeros: 8.25 -> '8.25', 10 -> '10', 0 -> '0'."""
    return "{:f}".format(Decimal(str(value)).normalize())


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        region = None
        discount_pct = 0
    else:
        customer_name = customer.name
        region = customer.region
        discount_pct = pricing.get_discount_pct(customer_id)
        if discount_pct is None:
            discount_pct = 0

    text_lines = ["Customer: {}".format(customer_name)]
    taxable_lines = []  # (category, amount_cents) for known skus only, in order
    subtotal = 0

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            text_lines.append("UNKNOWN SKU: {}".format(sku))
            continue
        unit_cents = item.price_cents
        amount_cents = unit_cents * quantity
        subtotal += amount_cents
        taxable_lines.append((item.category, amount_cents))
        text_lines.append("{} x{} @ {} = {}".format(
            sku, quantity, _money(unit_cents), _money(amount_cents)))

    discount_cents = _round_half_up(Decimal(subtotal) * Decimal(str(discount_pct)) / 100)

    if region is None:
        tax_cents = tax.compute_tax(None, discount_pct, taxable_lines)
        tax_pct = 0
    else:
        tax_cents = tax.compute_tax(region, discount_pct, taxable_lines)
        tax_pct = tax.rate_pct(region)

    total_cents = subtotal - discount_cents + tax_cents

    text_lines.append("Subtotal: {}".format(_money(subtotal)))
    text_lines.append("Discount ({}%): {}".format(_percent(discount_pct), _signed_money(discount_cents)))
    text_lines.append("Tax ({}%): {}".format(_percent(tax_pct), _money(tax_cents)))
    text_lines.append("Total: {}".format(_money(total_cents)))

    return "\n".join(text_lines)
