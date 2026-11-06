"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing


def _format_money(cents):
    return "$%d.%02d" % (cents // 100, cents % 100)


def _format_percent(value):
    # value is a decimal string such as "10", "8.25" or "0"; drop trailing zeros
    return format(Decimal(value).normalize(), "f")


def _percent_of_cents(cents, percent):
    # cents * percent / 100, rounded half up to the nearest cent
    amount = Decimal(cents) * Decimal(percent) / Decimal(100)
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer = pricing.lookup_customer(order["customer"])
    if customer is None:
        # unknown customer: show the id, no discount, no tax
        customer_name = order["customer"]
        discount_percent = "0"
        tax_percent = "0"
    else:
        customer_name = customer["name"]
        discount_percent = customer["discount_percent"]
        tax_percent = customer["tax_percent"]

    lines = ["Customer: %s" % customer_name]
    subtotal = 0
    for sku, quantity in order["lines"]:
        item = pricing.lookup_item(sku)
        if item is None:
            lines.append("UNKNOWN SKU: %s" % sku)
            continue
        amount = item["unit_price_cents"] * quantity
        subtotal += amount
        lines.append("%s x%d @ %s = %s" % (
            sku, quantity, _format_money(item["unit_price_cents"]), _format_money(amount)))

    discount = _percent_of_cents(subtotal, discount_percent)
    taxable = subtotal - discount
    tax = _percent_of_cents(taxable, tax_percent)
    total = taxable + tax

    lines.append("Subtotal: %s" % _format_money(subtotal))
    lines.append("Discount (%s%%): -%s" % (_format_percent(discount_percent), _format_money(discount)))
    lines.append("Tax (%s%%): %s" % (_format_percent(tax_percent), _format_money(tax)))
    lines.append("Total: %s" % _format_money(total))
    return "\n".join(lines)
