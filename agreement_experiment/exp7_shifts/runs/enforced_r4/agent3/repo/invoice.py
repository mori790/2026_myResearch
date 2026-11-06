"""Invoice module. Owned by agent3. Implement render_invoice(order).

Depends on the agreed APIs (see shared/agreement_log.jsonl):
  PRICING_API v1: pricing.get_item(sku) -> dict|None   {sku, name, price (float dollars), category}
                  pricing.get_customer(cust_id) -> dict|None {id, name, discount (fraction), region}
  TAX_API v1:     tax.dollars_to_cents(float) -> int cents
                  tax.calculate_tax(lines, customer) -> int cents
                  tax.tax_rate_pct(region) -> Decimal percent

Money inside this module is integer cents; it is formatted to dollars only for output.
Tax rules are NOT computed here; they come from tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as dollars, e.g. 1250 -> '$12.50'."""
    return "$%d.%02d" % (cents // 100, cents % 100)


def _percent(value):
    """Format a percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    lines_out = []
    tax_lines = []   # (category, amount_cents) for tax.py; unknown skus are excluded
    subtotal_cents = 0

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_label = customer_id
        discount_fraction = Decimal("0")
    else:
        customer_label = customer["name"]
        discount_fraction = Decimal(str(customer["discount"]))

    lines_out.append("Customer: %s" % customer_label)

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            lines_out.append("UNKNOWN SKU: %s" % sku)
            continue
        unit_cents = tax.dollars_to_cents(item["price"])
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        tax_lines.append((item["category"], amount_cents))
        lines_out.append("%s x%d @ %s = %s" % (sku, qty, _money(unit_cents), _money(amount_cents)))

    # Discount = subtotal * discount fraction, rounded to the cent, half up.
    discount_cents = int(
        (Decimal(subtotal_cents) * discount_fraction).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    # Tax amount and rate come from tax.py. Unknown customer -> no tax rules apply (0 tax, 0%).
    if customer is None:
        tax_cents = tax.calculate_tax(tax_lines, None)
        tax_percent = Decimal("0")
    else:
        tax_cents = tax.calculate_tax(tax_lines, customer)
        tax_percent = Decimal(str(tax.tax_rate_pct(customer["region"])))

    total_cents = subtotal_cents - discount_cents + tax_cents

    discount_percent = discount_fraction * 100
    lines_out.append("Subtotal: %s" % _money(subtotal_cents))
    lines_out.append("Discount (%s%%): -%s" % (_percent(discount_percent), _money(discount_cents)))
    lines_out.append("Tax (%s%%): %s" % (_percent(tax_percent), _money(tax_cents)))
    lines_out.append("Total: %s" % _money(total_cents))

    return "\n".join(lines_out)
