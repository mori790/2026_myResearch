"""Invoice module. Owned by agent3. Implement render_invoice(order).

Item and customer data come from pricing.py; all tax rules come from tax.py
(tax.tax_for_order). This module only does arithmetic and formatting.

Internal convention (team standard): money is decimal.Decimal in dollars,
percentages are multipliers. The cross-module interfaces use integer cents
and percent numbers (agreed with the tax and pricing owners), so conversion
happens here at the boundary only.
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _dollars(cents):
    """Integer cents -> Decimal dollars, e.g. 1250 -> Decimal('12.50')."""
    return (Decimal(cents) / HUNDRED).quantize(CENT)


def _money(amount):
    """Decimal dollars -> '$12.50'."""
    return "$" + str(amount.quantize(CENT, rounding=ROUND_HALF_UP))


def _signed_money(amount):
    """Non-negative Decimal dollars -> '-$3.91'."""
    return "-" + _money(amount)


def _percent_text(percent):
    """Percent number -> text without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(percent)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.lookup_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, no region (so 0% tax).
        customer_name = customer_id
        region = None
        discount_pct = 0
    else:
        customer_name = customer.name or customer_id
        region = customer.region
        discount_pct = customer.discount_pct

    lines_out = ["Customer: " + customer_name]
    tax_lines = []  # (category, amount_cents) for known SKUs, before discount
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = pricing.lookup_item(sku)
        if item is None:
            lines_out.append("UNKNOWN SKU: " + str(sku))
            continue
        line_cents = item.unit_price_cents * quantity
        subtotal_cents += line_cents
        tax_lines.append((item.category, line_cents))
        lines_out.append(
            "{} x{} @ {} = {}".format(
                sku, quantity, _money(_dollars(item.unit_price_cents)), _money(_dollars(line_cents))
            )
        )

    # Discount = subtotal x discount percent, rounded to the cent (half up).
    discount_cents = int(
        (Decimal(subtotal_cents) * Decimal(str(discount_pct)) / HUNDRED).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )

    # All tax rules (exemptions, rates, rounding) are decided by tax.py.
    tax_result = tax.tax_for_order(tax_lines, region, discount_pct)
    tax_cents = tax_result.tax_cents

    total_cents = subtotal_cents - discount_cents + tax_cents

    lines_out.append("Subtotal: " + _money(_dollars(subtotal_cents)))
    lines_out.append(
        "Discount ({}%): {}".format(
            _percent_text(discount_pct), _signed_money(_dollars(discount_cents))
        )
    )
    lines_out.append(
        "Tax ({}%): {}".format(_percent_text(tax_result.tax_pct), _money(_dollars(tax_cents)))
    )
    lines_out.append("Total: " + _money(_dollars(total_cents)))
    return "\n".join(lines_out)
