"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).
"""

from decimal import Decimal

import pricing


def _money(cents):
    return "${}.{:02d}".format(cents // 100, cents % 100)


def _pct(value):
    # Show percents without trailing zeros: 10 -> "10", 8.25 -> "8.25", 0 -> "0".
    return format(Decimal(value).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    try:
        customer = pricing.get_customer(customer_id)
    except pricing.UnknownCustomerError:
        customer = None

    out = []
    if customer is None:
        out.append("Customer: {}".format(customer_id))
    else:
        out.append("Customer: {}".format(customer.name))

    subtotal_cents = 0
    for sku, qty in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except pricing.UnknownSkuError:
            out.append("UNKNOWN SKU: {}".format(sku))
            continue
        amount_cents = pricing.line_total_cents(sku, qty)
        subtotal_cents += amount_cents
        out.append("{} x{} @ {} = {}".format(
            sku, qty, _money(item.price_cents), _money(amount_cents)))

    if customer is None:
        discount_pct = Decimal(0)
        discount_cents = 0
        tax_pct = Decimal(0)
        tax_cents = 0
    else:
        discount_pct = customer.discount_pct
        discount_cents = pricing.discount_cents(subtotal_cents, customer_id)
        tax_pct = pricing.get_tax_pct(customer.region)
        tax_cents = pricing.tax_cents(subtotal_cents - discount_cents, customer.region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: {}".format(_money(subtotal_cents)))
    out.append("Discount ({}%): -{}".format(_pct(discount_pct), _money(discount_cents)))
    out.append("Tax ({}%): {}".format(_pct(tax_pct), _money(tax_cents)))
    out.append("Total: {}".format(_money(total_cents)))

    return "\n".join(out)
