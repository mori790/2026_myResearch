"""Invoice module. Owned by agent3.

render_invoice(order) gets all item, customer and tax information from
pricing.py and tax.py. It computes no tax rules itself.

Committed interfaces used (see agree.py lookup):
  money_units:     all money amounts are int cents; percents are Decimal.
  pricing_api_v2:  pricing.get_item(sku) -> {"sku", "name", "unit_price_cents", "category"} | None
                   pricing.get_customer(customer_id) -> {"id", "name", "region", "discount_percent"} | None
  tax_api v2:      tax.compute_tax(lines, region, discount_pct) -> dict with
                   taxable_cents, discount_cents, tax_pct, tax_cents
                   lines = [{"category": str, "amount_cents": int}] (gross line totals)

Deviation (announced on tax_api): the Discount line is computed here as
round_half_up(subtotal * discount_percent / 100), as the invoice spec requires.
tax's discount_cents (taxable base only) is not displayed.
"""

import pricing
import tax
from decimal import Decimal, ROUND_HALF_UP


def _money(cents):
    """Format int cents as a dollar string with a leading '$' (e.g. 2500 -> '$25.00')."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s$%d.%02d" % (sign, cents // 100, cents % 100)


def _percent(value):
    """Format a percent without trailing zeros (10 -> '10', Decimal('8.25') -> '8.25', 0 -> '0')."""
    d = Decimal(str(value))
    text = format(d, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text if text else "0"


def _round_half_up_cents(numerator_cents, percent):
    """Return round_half_up(numerator_cents * percent / 100) as an int number of cents."""
    value = Decimal(numerator_cents) * Decimal(str(percent)) / Decimal(100)
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (no region).
        customer_name = customer_id
        region = None
        discount_percent = 0
    else:
        customer_name = customer["name"]
        region = customer["region"]
        discount_percent = customer["discount_percent"]

    out_lines = ["Customer: %s" % customer_name]
    tax_lines = []  # gross line totals for tax.py, known SKUs only
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: %s" % sku)
            continue
        unit_price_cents = item["unit_price_cents"]
        amount_cents = unit_price_cents * quantity
        subtotal_cents += amount_cents
        tax_lines.append({"category": item["category"], "amount_cents": amount_cents})
        out_lines.append(
            "%s x%d @ %s = %s" % (sku, quantity, _money(unit_price_cents), _money(amount_cents))
        )

    discount_cents = _round_half_up_cents(subtotal_cents, discount_percent)

    tax_result = tax.compute_tax(tax_lines, region, discount_percent)
    tax_pct = tax_result["tax_pct"]
    tax_cents = tax_result["tax_cents"]

    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append("Subtotal: %s" % _money(subtotal_cents))
    out_lines.append("Discount (%s%%): -%s" % (_percent(discount_percent), _money(discount_cents)))
    out_lines.append("Tax (%s%%): %s" % (_percent(tax_pct), _money(tax_cents)))
    out_lines.append("Total: %s" % _money(total_cents))

    return "\n".join(out_lines)
