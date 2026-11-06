"""Invoice module. Owned by agent3. Implement render_invoice(order).

All item, customer and tax information comes from pricing.py and tax.py.
Money is integer cents; percents are decimal.Decimal.
"""

from decimal import Decimal

import pricing
import tax


def _money(cents):
    """Format a non-negative integer amount of cents as $X.YY."""
    return "$%d.%02d" % (cents // 100, cents % 100)


def _pct(value):
    """Format a Decimal percent without trailing zeros (10, 8.25, 0)."""
    return format(Decimal(value).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]

    # Customer lookup. An unknown customer is shown by its id with 0% discount and 0% tax.
    try:
        customer = pricing.get_customer(customer_id)
    except KeyError:  # UnknownCustomerError subclasses KeyError
        customer = None

    if customer is not None:
        name = customer.name
        region = customer.region
        discount_pct = Decimal(customer.discount_pct)
    else:
        name = customer_id
        region = None
        discount_pct = Decimal("0")

    out = ["Customer: %s" % name]

    # Lines. Unknown SKUs are listed in place and skipped in the totals.
    subtotal = 0
    taxable_lines = []  # (category, line_cents) for known SKUs only
    for sku, quantity in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:  # UnknownSKUError subclasses KeyError
            out.append("UNKNOWN SKU: %s" % sku)
            continue
        amount = item.price_cents * quantity
        out.append("%s x%d @ %s = %s" % (sku, quantity, _money(item.price_cents), _money(amount)))
        subtotal += amount
        taxable_lines.append((item.category, amount))

    # Discount: subtotal * discount percent, rounded half-up to the cent (done by pricing.py).
    if customer is not None:
        discount = pricing.discount_cents(customer_id, subtotal)
    else:
        discount = 0

    # Tax amount and percent come from tax.py.
    tax_pct, tax_cents = tax.compute_tax(region, taxable_lines, discount_pct)
    tax_pct = Decimal(tax_pct)

    total = subtotal - discount + tax_cents

    out.append("Subtotal: %s" % _money(subtotal))
    out.append("Discount (%s%%): -%s" % (_pct(discount_pct), _money(discount)))
    out.append("Tax (%s%%): %s" % (_pct(tax_pct), _money(tax_cents)))
    out.append("Total: %s" % _money(total))

    return "\n".join(out)
