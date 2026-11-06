"""Invoice module. Owned by agent3.

render_invoice(order) gets all item, customer and tax information from
pricing.py and tax.py (see committed decisions pricing.api,
pricing.money_and_percent_units and tax.api). It applies no tax rules itself.

Internal money math uses decimal.Decimal in dollars. Values coming from
pricing.py and tax.py are floats (dollars, or fractions for percentages) and
are converted with repr() so no binary float error creeps in.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _to_decimal(value):
    """Convert a float (or int/str) from another module to an exact Decimal."""
    return Decimal(repr(float(value)))


def _round_cent(amount):
    """Round a Decimal to the cent, half up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal dollar amount as '$12.50' (no sign)."""
    return "$" + format(_round_cent(amount), ".2f")


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros: 0.0825 -> '8.25', 0.1 -> '10', 0 -> '0'."""
    percent = (_to_decimal(fraction) * HUNDRED).normalize()
    return format(percent, "f")


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, no discount, no tax.
        customer_name = customer_id
        discount_fraction = 0.0
        region = None
    else:
        customer_name = customer.get("name") or customer_id
        discount_fraction = customer.get("discount", 0.0)
        region = customer.get("region")

    out_lines = ["Customer: " + str(customer_name)]

    # Known items: (sku, quantity, unit price, line amount, category)
    taxable_input = []
    subtotal = Decimal("0")

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: " + str(sku))
            continue

        unit_price = _round_cent(_to_decimal(item["price"]))
        line_amount = unit_price * quantity
        subtotal += line_amount

        out_lines.append(
            "{} x{} @ {} = {}".format(sku, quantity, _money(unit_price), _money(line_amount))
        )
        taxable_input.append({"category": item.get("category", ""), "amount": float(line_amount)})

    discount_amount = _round_cent(subtotal * _to_decimal(discount_fraction))

    # tax.py decides taxability and does all tax rounding.
    tax_amount = _round_cent(_to_decimal(tax.compute_tax(region, float(discount_fraction), taxable_input)))
    tax_percent = _percent(tax.tax_rate(region))

    total = subtotal - discount_amount + tax_amount

    out_lines.append("Subtotal: " + _money(subtotal))
    out_lines.append("Discount (" + _percent(discount_fraction) + "%): -" + _money(discount_amount))
    out_lines.append("Tax (" + tax_percent + "%): " + _money(tax_amount))
    out_lines.append("Total: " + _money(total))

    return "\n".join(out_lines)
