"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed pricing_api v2 and the accepted tax_api v3:
  pricing.get_item(sku)           -> {sku, name, price_cents:int, category} or None
  pricing.get_customer(cid)       -> {id, name, discount_pct:number (10 = 10%), region} or None
  tax.compute_tax(lines, region, discount_pct) -> TaxResult(taxable_cents, discount_pct, tax_pct, tax_cents)
    lines: [{amount_cents:int, category:str}] for known items only
    region: None for an unknown customer (0% tax)

Money is int cents throughout; percentages are percent numbers (10 = 10%).
invoice.py does not compute any tax rule itself.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _half_up_cents(value):
    """Round a Decimal number of cents to an int, half up."""
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format int cents as a dollar string: 1250 -> '$12.50'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s$%d.%02d" % (sign, cents // 100, cents % 100)


def _percent(value):
    """Format a percent number without trailing zeros: 8.25 -> '8.25', 10 -> '10', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        customer_label = customer_id
        region = None
        discount_pct = 0
    else:
        customer_label = customer["name"]
        region = customer["region"]
        discount_pct = customer["discount_pct"]

    out = ["Customer: " + customer_label]

    known_lines = []  # passed to tax.py: {amount_cents, category}
    subtotal_cents = 0
    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: " + str(sku))
            continue
        amount_cents = item["price_cents"] * qty
        subtotal_cents += amount_cents
        known_lines.append({"amount_cents": amount_cents, "category": item["category"]})
        out.append("%s x%d @ %s = %s" % (
            sku, qty, _money(item["price_cents"]), _money(amount_cents)))

    discount_cents = _half_up_cents(
        Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100))

    result = tax.compute_tax(known_lines, region, discount_pct)
    tax_cents = result.tax_cents
    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: " + _money(subtotal_cents))
    out.append("Discount (%s%%): -%s" % (_percent(discount_pct), _money(discount_cents)))
    out.append("Tax (%s%%): %s" % (_percent(result.tax_pct), _money(tax_cents)))
    out.append("Total: " + _money(total_cents))
    return "\n".join(out)
