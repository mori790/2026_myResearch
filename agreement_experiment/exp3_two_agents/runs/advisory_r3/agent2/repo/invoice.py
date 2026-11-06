"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).
"""

from decimal import Decimal

import pricing


def _money(cents):
    return "$%d.%02d" % (cents // 100, cents % 100)


def _percent(value):
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    try:
        customer = pricing.get_customer(customer_id)
    except KeyError:
        customer = None

    if customer is None:
        lines = ["Customer: " + customer_id]
    else:
        lines = ["Customer: " + customer["name"]]

    subtotal = 0
    for sku, quantity in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            lines.append("UNKNOWN SKU: " + sku)
            continue
        unit_price = item["unit_price_cents"]
        amount = unit_price * quantity
        subtotal += amount
        lines.append("%s x%s @ %s = %s" % (sku, quantity, _money(unit_price), _money(amount)))

    if customer is None:
        discount_pct = "0"
        tax_pct = "0"
        discount = 0
        tax = 0
    else:
        region = customer["region"]
        discount_pct = _percent(customer["discount_pct"])
        tax_pct = _percent(pricing.get_tax_pct(region))
        discount = pricing.discount_cents(subtotal, customer_id)
        tax = pricing.tax_cents(subtotal - discount, region)

    total = subtotal - discount + tax
    lines.append("Subtotal: " + _money(subtotal))
    lines.append("Discount (%s%%): -%s" % (discount_pct, _money(discount)))
    lines.append("Tax (%s%%): %s" % (tax_pct, _money(tax)))
    lines.append("Total: " + _money(total))
    return "\n".join(lines)
