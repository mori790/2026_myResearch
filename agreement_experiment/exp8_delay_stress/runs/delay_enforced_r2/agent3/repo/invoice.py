"""Invoice module. Owned by agent3. Implement render_invoice(order).

Conventions (committed in the shared decision log):
  PRICING_API v1: get_item(sku) -> dict {sku, name, unit_price (float dollars), category} or None on a miss;
                  get_customer(customer_id) -> dict {id, name, discount (fraction, 0.10 = 10%), region} or None.
  TAX_API v2:     tax.get_sales_tax(region, lines, discount) where lines is a list of
                  {"category": str, "amount": float dollars before discount} for known items;
                  returns {"rate": float fraction, "tax": float dollars} or None (treated as 0% / $0.00).
                  Region None means unknown customer -> 0 tax.

invoice.py does the money arithmetic on the invoice level (line amounts, subtotal, discount, total).
It does not compute any tax rule; the tax base and the discount on the taxable base are tax.py's job.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(value):
    """Convert a float (dollars) or Decimal to a Decimal rounded half-up to the cent."""
    if not isinstance(value, Decimal):
        value = Decimal(repr(float(value)))
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _fmt_money(amount):
    """Format a Decimal amount as $12.50 (no sign handling; callers add '-' where needed)."""
    return "$" + format(_money(amount), ".2f")


def _fmt_percent(fraction):
    """Format a fraction as a percent without trailing zeros: 0.1 -> '10', 0.0825 -> '8.25', 0 -> '0'."""
    value = Decimal(repr(float(fraction))) * 100
    text = format(value.normalize(), "f")
    return text


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_fraction = 0.0
        region = None
    else:
        customer_name = customer["name"]
        discount_fraction = customer["discount"]
        region = customer["region"]

    out_lines = ["Customer: " + customer_name]

    subtotal = Decimal("0.00")
    taxable_lines = []  # for tax.py: {"category", "amount"} for known items only

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: " + str(sku))
            continue
        unit_price = _money(item["unit_price"])
        line_amount = _money(unit_price * Decimal(int(quantity)))
        subtotal += line_amount
        out_lines.append(
            "{} x{} @ {} = {}".format(sku, quantity, _fmt_money(unit_price), _fmt_money(line_amount))
        )
        taxable_lines.append({"category": item["category"], "amount": float(line_amount)})

    discount_amount = _money(subtotal * Decimal(repr(float(discount_fraction))))

    # tax.py returns None for an unknown region; treat that as 0% tax and $0.00.
    tax_result = tax.get_sales_tax(region, taxable_lines, float(discount_fraction))
    if tax_result is None:
        tax_rate = 0.0
        tax_amount = Decimal("0.00")
    else:
        tax_rate = tax_result["rate"]
        tax_amount = _money(tax_result["tax"])

    total = subtotal - discount_amount + tax_amount

    out_lines.append("Subtotal: " + _fmt_money(subtotal))
    out_lines.append(
        "Discount ({}%): -{}".format(_fmt_percent(discount_fraction), _fmt_money(discount_amount))
    )
    out_lines.append("Tax ({}%): {}".format(_fmt_percent(tax_rate), _fmt_money(tax_amount)))
    out_lines.append("Total: " + _fmt_money(total))

    return "\n".join(out_lines)
