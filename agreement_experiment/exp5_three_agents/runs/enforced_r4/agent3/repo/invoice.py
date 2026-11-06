"""Invoice module. Owned by agent3. Implement render_invoice(order).

Depends on (agreed in the shared agreement log, topics pricing_api and tax_api):
  pricing.get_item(sku) -> Item(sku, name, price_cents, category); raises pricing.UnknownSKU
  pricing.get_customer(customer_id) -> Customer(id, name, discount_pct, region); raises pricing.UnknownCustomer
  pricing.discounted_price_cents(unit_price_cents, discount_pct) -> int cents
  tax.calculate_tax(lines, region) -> int cents, lines = [(category, amount_cents)]
  tax.get_rate_percent(region) -> Decimal

All money inside this module is integer cents. Discount is computed here from the
undiscounted subtotal (spec rule); tax rules are never computed here.
"""

from decimal import Decimal

import pricing
import tax


def _round_half_up_div(numerator, denominator):
    """Integer division rounding half up (numerator and denominator >= 0)."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder >= denominator:
        quotient += 1
    return quotient


def _money(cents):
    """Format non-negative integer cents as $X.YY."""
    return "$%d.%02d" % divmod(cents, 100)


def _signed_money(cents):
    """Format a non-negative amount as -$X.YY (used for discount)."""
    return "-" + _money(cents)


def _percent(value):
    """Show a percent without trailing zeros: 10, 8.25, 0."""
    return format(Decimal(value).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]

    try:
        customer = pricing.get_customer(customer_id)
        name = customer.name
        discount_pct = int(customer.discount_pct)
        region = customer.region
    except pricing.UnknownCustomer:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        name = customer_id
        discount_pct = 0
        region = None

    # Known lines, in order. Unknown SKUs keep their position as a text marker.
    output_lines = ["Customer: %s" % name]
    priced_lines = []  # (category, discounted_line_cents) for tax.py
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except pricing.UnknownSKU:
            output_lines.append("UNKNOWN SKU: %s" % sku)
            continue

        line_cents = item.price_cents * quantity
        subtotal_cents += line_cents
        output_lines.append(
            "%s x%d @ %s = %s" % (sku, quantity, _money(item.price_cents), _money(line_cents))
        )

        discounted_unit = pricing.discounted_price_cents(item.price_cents, discount_pct)
        priced_lines.append((item.category, discounted_unit * quantity))

    discount_cents = _round_half_up_div(subtotal_cents * discount_pct, 100)
    tax_cents = tax.calculate_tax(priced_lines, region)
    tax_percent = _percent(tax.get_rate_percent(region))
    total_cents = subtotal_cents - discount_cents + tax_cents

    output_lines.append("Subtotal: %s" % _money(subtotal_cents))
    output_lines.append("Discount (%d%%): %s" % (discount_pct, _signed_money(discount_cents)))
    output_lines.append("Tax (%s%%): %s" % (tax_percent, _money(tax_cents)))
    output_lines.append("Total: %s" % _money(total_cents))

    return "\n".join(output_lines)
