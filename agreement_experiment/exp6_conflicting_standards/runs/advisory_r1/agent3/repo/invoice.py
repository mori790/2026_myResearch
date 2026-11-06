"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed team decisions:
  - money_unit v3: money is float dollars (converted to Decimal here only for exact cent rounding)
  - percent_unit v1: percentages are fractions (0.10 = 10 percent)
  - missing_lookup_signal v1: a lookup that finds nothing returns None
  - pricing_api v1: pricing.get_item(sku) / pricing.get_customer(customer_id)
  - tax_api v2: tax.compute_tax(region, lines) -> {"rate": float, "tax": float}

This module computes no tax rules itself; all tax information comes from tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _money(value):
    """Decimal dollars rounded to the cent (half up)."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _fmt_money(amount):
    """Format a Decimal dollar amount as $12.50 (no thousands separator)."""
    if amount < 0:
        return "-$" + format(-amount, "f")
    return "$" + format(amount, "f")


def _fmt_percent(fraction):
    """Format a fraction as a percent without trailing zeros: 0.1 -> '10', 0.0825 -> '8.25', 0 -> '0'."""
    percent = Decimal(str(fraction)) * HUNDRED
    text = format(percent.normalize(), "f")
    return text


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        customer_name = customer_id
        discount_rate = 0.0
        region = None
    else:
        customer_name = customer["name"]
        discount_rate = customer["discount_rate"]
        region = customer["region"]

    discount_fraction = Decimal(str(discount_rate))
    multiplier = Decimal("1") - discount_fraction

    out = ["Customer: " + customer_name]

    # Known items: (sku, quantity, unit_price, line_amount, category)
    known = []
    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: " + sku)
            continue
        unit_price = Decimal(str(item["unit_price"]))
        line_amount = _money(unit_price * quantity)
        out.append(
            "{} x{} @ {} = {}".format(
                sku, quantity, _fmt_money(_money(unit_price)), _fmt_money(line_amount)
            )
        )
        known.append((sku, quantity, unit_price, line_amount, item["category"]))

    subtotal = sum((line[3] for line in known), Decimal("0.00"))
    subtotal = _money(subtotal)
    discount = _money(subtotal * discount_fraction)

    # tax_api v2: net_amount is the line amount after the customer discount, unrounded.
    tax_lines = []
    for sku, quantity, unit_price, _line_amount, category in known:
        net = unit_price * quantity * multiplier
        tax_lines.append({"sku": sku, "category": category, "net_amount": float(net)})

    tax_result = tax.compute_tax(region, tax_lines)
    tax_rate = tax_result["rate"]
    tax_amount = _money(Decimal(str(tax_result["tax"])))

    total = _money(subtotal - discount + tax_amount)

    out.append("Subtotal: " + _fmt_money(subtotal))
    out.append("Discount ({}%): -{}".format(_fmt_percent(discount_fraction), _fmt_money(discount)))
    out.append("Tax ({}%): {}".format(_fmt_percent(tax_rate), _fmt_money(tax_amount)))
    out.append("Total: " + _fmt_money(total))

    return "\n".join(out)
