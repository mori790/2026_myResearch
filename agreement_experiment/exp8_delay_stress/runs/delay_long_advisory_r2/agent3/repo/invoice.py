"""Invoice module. Owned by agent3. Implement render_invoice(order).

Follows the committed team decisions:
  - pricing_api v2: pricing.get_item(sku) -> {"sku","name","price"(int cents),"category"} or None;
                    pricing.get_customer(cid) -> {"id","name","discount"(percent number),"region"} or None.
  - TAX_API v1:     tax.compute_tax(lines, region, discount_pct) -> int cents,
                    lines = [(category, amount_cents)] before tax and discount;
                    tax.tax_pct(region) -> float percent number.
  - TAX_UNKNOWN_CUSTOMER v1: region None (unknown customer) -> 0 tax.

Money inside this module is integer cents; it is formatted as dollars only for output.
Percents are plain percent numbers (10 means 10%).
This module does not compute any tax rule itself.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _cents_to_money(cents):
    """Format an integer amount of cents as '$12.50' (or '-$3.91' when negative)."""
    sign = "-" if cents < 0 else ""
    magnitude = abs(cents)
    return "{}${}.{:02d}".format(sign, magnitude // 100, magnitude % 100)


def _format_percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0.0 -> '0'."""
    text = format(Decimal(str(value)).normalize(), "f")
    return text


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * discount percent / 100, rounded to the cent, half up."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (TAX_UNKNOWN_CUSTOMER: region None -> 0 tax).
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = customer["discount"]
        region = customer["region"]

    output_lines = ["Customer: {}".format(customer_name)]

    subtotal_cents = 0
    tax_lines = []  # (category, amount_cents) for known skus only, before tax and discount

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            output_lines.append("UNKNOWN SKU: {}".format(sku))
            continue

        unit_price = item["price"]
        line_amount = unit_price * quantity
        subtotal_cents += line_amount
        tax_lines.append((item["category"], line_amount))

        output_lines.append("{} x{} @ {} = {}".format(
            sku, quantity, _cents_to_money(unit_price), _cents_to_money(line_amount)))

    discount_cents = _discount_cents(subtotal_cents, discount_pct)

    if region is None:
        tax_cents = 0
        tax_pct_text = "0"
    else:
        tax_cents = tax.compute_tax(tax_lines, region, discount_pct)
        tax_pct_text = _format_percent(tax.tax_pct(region))

    total_cents = subtotal_cents - discount_cents + tax_cents

    output_lines.append("Subtotal: {}".format(_cents_to_money(subtotal_cents)))
    # Discount line always shows a minus sign, including "-$0.00".
    output_lines.append("Discount ({}%): -{}".format(
        _format_percent(discount_pct), _cents_to_money(discount_cents).lstrip("-")))
    output_lines.append("Tax ({}%): {}".format(tax_pct_text, _cents_to_money(tax_cents)))
    output_lines.append("Total: {}".format(_cents_to_money(total_cents)))

    return "\n".join(output_lines)
