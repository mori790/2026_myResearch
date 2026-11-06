"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed team interfaces only:
  pricing.get_item(sku)          -> dict {sku, name, unit_price, category} or None
  pricing.get_customer(cid)      -> dict {id, name, discount, region} or None
  tax.tax_percent(region)        -> percent number (e.g. 8.25), 0 for None region
  tax.compute_tax(lines, region, discount)
                                 -> tax in float dollars, lines are
                                    (undiscounted amount, category)

Money is handled internally as Decimal; values from other modules are
float dollars/fractions and are converted via str() to avoid float noise.
Invoice never applies tax or exemption rules itself.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(value):
    """Round a Decimal-convertible value to the cent (half up)."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _fmt_money(value):
    """Format a Decimal amount as $12.50 (negative amounts as -$3.91)."""
    amount = _money(value)
    if amount < 0:
        return "-$" + format(-amount, "f")
    return "$" + format(amount, "f")


def _fmt_percent(number):
    """Format a percent number without trailing zeros: 10, 8.25, 0."""
    d = Decimal(str(number)).normalize()
    return format(d, "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, no discount, no tax.
        customer_label = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_label = customer["name"]
        discount_fraction = Decimal(str(customer["discount"]))
        region = customer["region"]

    lines_out = ["Customer: " + customer_label]
    taxable_lines = []  # (undiscounted amount as float dollars, category)
    subtotal = Decimal("0")

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            lines_out.append("UNKNOWN SKU: " + str(sku))
            continue

        unit_price = _money(item["unit_price"])
        line_amount = unit_price * quantity
        subtotal += line_amount
        lines_out.append(
            "{} x{} @ {} = {}".format(
                sku, quantity, _fmt_money(unit_price), _fmt_money(line_amount)
            )
        )
        taxable_lines.append((float(line_amount), item["category"]))

    discount = _money(subtotal * discount_fraction)
    tax_amount = _money(tax.compute_tax(taxable_lines, region, float(discount_fraction)))
    tax_percent = tax.tax_percent(region)

    total = subtotal - discount + tax_amount

    lines_out.append("Subtotal: " + _fmt_money(subtotal))
    lines_out.append(
        "Discount ({}%): -{}".format(
            _fmt_percent(discount_fraction * 100), _fmt_money(discount).lstrip("-")
        )
    )
    lines_out.append(
        "Tax ({}%): {}".format(_fmt_percent(tax_percent), _fmt_money(tax_amount))
    )
    lines_out.append("Total: " + _fmt_money(total))

    return "\n".join(lines_out)
