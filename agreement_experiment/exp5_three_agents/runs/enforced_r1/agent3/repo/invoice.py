"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed decisions:
  PRICING_API v2: pricing.get_item(sku) -> Item(sku, name, price_cents, category), KeyError if unknown
                  pricing.get_customer(id) -> Customer(id, name, discount_pct, region), KeyError if unknown
  tax_api v2:     tax.compute_tax(lines, region, discount_pct) -> int cents of tax only
                  tax.tax_rate_percent(region) -> Decimal percent for the "Tax (x%)" label

Money is integer cents everywhere. invoice.py computes the discount itself (half up)
and never computes tax rules.
"""

from decimal import Decimal

import pricing
import tax


def _money(cents):
    """Format non-negative integer cents as $X.YY."""
    return "$%d.%02d" % (cents // 100, cents % 100)


def _percent(value):
    """Format a percent without trailing zeros: 10, 8.25, 0."""
    return format(Decimal(value).normalize(), "f")


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * pct / 100 rounded to the cent, half up (integer arithmetic)."""
    return (subtotal_cents * discount_pct + 50) // 100


def render_invoice(order):
    customer_id = order["customer"]

    # Unknown customer: shown by id, 0% discount, region None (tax gives 0%).
    try:
        customer = pricing.get_customer(customer_id)
        customer_name = customer.name
        discount_pct = customer.discount_pct
        region = customer.region
    except KeyError:
        customer_name = customer_id
        discount_pct = 0
        region = None

    out = ["Customer: %s" % customer_name]
    subtotal_cents = 0
    tax_lines = []  # (category, pre-discount line amount in cents)

    for sku, qty in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            out.append("UNKNOWN SKU: %s" % sku)
            continue

        amount_cents = item.price_cents * qty
        subtotal_cents += amount_cents
        tax_lines.append((item.category, amount_cents))
        out.append("%s x%d @ %s = %s" % (
            sku, qty, _money(item.price_cents), _money(amount_cents)))

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    tax_cents = tax.compute_tax(tax_lines, region, discount_pct)
    tax_rate = _percent(tax.tax_rate_percent(region))
    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: %s" % _money(subtotal_cents))
    out.append("Discount (%s%%): -%s" % (_percent(discount_pct), _money(discount_cents)))
    out.append("Tax (%s%%): %s" % (tax_rate, _money(tax_cents)))
    out.append("Total: %s" % _money(total_cents))

    return "\n".join(out)
