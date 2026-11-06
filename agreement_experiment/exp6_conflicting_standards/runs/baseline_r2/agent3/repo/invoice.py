"""Invoice module. Owned by agent3. Implement render_invoice(order).

Money inside this module is decimal.Decimal in dollars (team standard).
Percentages shown to the user are percent numbers (10 -> "10%").
Calls into other modules:
  pricing.get_item(sku)          -> Item | None   (Item.price float dollars, Item.category)
  pricing.get_customer(cid)      -> Customer | None (Customer.name, Customer.discount_rate fraction, Customer.region)
  tax.compute_tax(region, lines, discount_pct) -> int cents
  tax.tax_pct(region)            -> percent number (8.25 for 8.25%)
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")
ZERO = Decimal("0")


def _money(amount):
    """Round a Decimal dollar amount to the cent, half up."""
    return Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP)


def _fmt_money(amount):
    """Format as $12.50. Negative amounts are shown as -$3.91."""
    value = _money(amount)
    if value < 0:
        return "-$" + format(-value, ".2f")
    return "$" + format(value, ".2f")


def _fmt_percent(percent):
    """Format a percent number without trailing zeros: 10, 8.25, 0."""
    text = format(Decimal(percent).normalize(), "f")
    return text


def _to_decimal(value):
    """Convert a float/int/str from another module to Decimal without binary noise."""
    return Decimal(str(value))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_pct = ZERO
        region = None
    else:
        customer_name = customer.name
        discount_pct = _to_decimal(customer.discount_rate) * HUNDRED
        region = customer.region

    output = ["Customer: " + str(customer_name)]

    subtotal = ZERO
    taxable_lines = []  # (category, amount in integer cents) for tax.compute_tax

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output.append("UNKNOWN SKU: " + str(sku))
            continue

        unit_price = _to_decimal(item.price)
        amount = _money(unit_price * quantity)
        subtotal += amount
        output.append(
            "{} x{} @ {} = {}".format(sku, quantity, _fmt_money(unit_price), _fmt_money(amount))
        )
        taxable_lines.append((item.category, int(amount * 100)))

    subtotal = _money(subtotal)

    if customer is None:
        discount = _money(ZERO)
        discount_pct_for_tax = 0
    else:
        discount = _money(subtotal * _to_decimal(customer.discount_rate))
        discount_pct_for_tax = float(discount_pct)

    tax_cents = tax.compute_tax(region, taxable_lines, discount_pct_for_tax)
    tax_amount = _money(Decimal(tax_cents) / HUNDRED)

    if region is None:
        tax_percent = ZERO
    else:
        tax_percent = _to_decimal(tax.tax_pct(region))

    total = _money(subtotal - discount + tax_amount)

    output.append("Subtotal: " + _fmt_money(subtotal))
    output.append("Discount ({}%): -{}".format(_fmt_percent(discount_pct), _fmt_money(discount)))
    output.append("Tax ({}%): {}".format(_fmt_percent(tax_percent), _fmt_money(tax_amount)))
    output.append("Total: " + _fmt_money(total))

    return "\n".join(output)
