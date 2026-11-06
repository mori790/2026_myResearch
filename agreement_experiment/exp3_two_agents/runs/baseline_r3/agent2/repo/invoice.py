"""Invoice module. Owned by agent2 (the invoice developer).

Implement render_invoice(order). Get all item and customer information by
calling agent1's pricing module (import pricing).

Pricing API (agreed with agent1):
  get_item(sku)             -> {'sku', 'name', 'price_cents'}; KeyError if unknown
  get_customer(customer_id) -> {'id', 'name', 'discount_pct', 'region'}; KeyError if unknown
  get_tax_pct(region)       -> number (0 if the region has no tax row)
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing


def _money(cents):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "{}${}.{:02d}".format(sign, cents // 100, cents % 100)


def _percent_text(value):
    # Decimal(str(...)) keeps the exact decimal value; normalize() drops
    # trailing zeros, and format 'f' avoids exponent notation (10 -> "10").
    return format(Decimal(str(value)).normalize(), "f")


def _percent_cents(base_cents, percent):
    # base * percent / 100, rounded to the cent, half up.
    amount = Decimal(base_cents) * Decimal(str(percent)) / Decimal(100)
    return int(amount.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def render_invoice(order):
    lines = []

    try:
        customer = pricing.get_customer(order["customer"])
    except KeyError:
        customer = None

    if customer is None:
        customer_name = str(order["customer"])
        discount_pct = 0
        tax_pct = 0
    else:
        customer_name = customer["name"]
        discount_pct = customer["discount_pct"]
        tax_pct = pricing.get_tax_pct(customer["region"])

    lines.append("Customer: {}".format(customer_name))

    subtotal_cents = 0
    for sku, quantity in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            lines.append("UNKNOWN SKU: {}".format(sku))
            continue
        line_cents = item["price_cents"] * quantity
        subtotal_cents += line_cents
        lines.append("{} x{} @ {} = {}".format(
            sku, quantity, _money(item["price_cents"]), _money(line_cents)))

    discount_cents = _percent_cents(subtotal_cents, discount_pct)
    taxable_cents = subtotal_cents - discount_cents
    tax_cents = _percent_cents(taxable_cents, tax_pct)
    total_cents = taxable_cents + tax_cents

    lines.append("Subtotal: {}".format(_money(subtotal_cents)))
    lines.append("Discount ({}%): -{}".format(
        _percent_text(discount_pct), _money(discount_cents)))
    lines.append("Tax ({}%): {}".format(
        _percent_text(tax_pct), _money(tax_cents)))
    lines.append("Total: {}".format(_money(total_cents)))

    return "\n".join(lines)
