"""Invoice module. Owned by agent3. Implement render_invoice(order).

Committed APIs (agreement log: pricing_api v2, tax_api v1):
  pricing.get_item(sku)            -> {sku, name, price (float dollars), category} or None
  pricing.get_customer(cid)        -> {id, name, discount (fraction OFF, 0.10 = 10%), region} or None
  tax.compute_tax(lines, region, discount_pct)
      lines        -> [{category, amount_cents}] (line amounts before discount, integer cents)
      region       -> str, or None for an unknown customer (tax 0)
      discount_pct -> number, percent (10 means 10%)
      returns      -> {taxable_cents, tax_cents, tax_pct}

Money is handled as integer cents internally. This module applies no tax rules;
all tax amounts and rates come from tax.compute_tax.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(amount):
    """Float dollars -> integer cents, rounded half up."""
    return int((Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Integer cents (non-negative) -> '$12.50'."""
    return "$%d.%02d" % (cents // 100, cents % 100)


def _percent(value):
    """Number -> text without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None).
        customer_name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_name = customer["name"]
        discount_fraction = Decimal(str(customer["discount"]))
        region = customer["region"]

    discount_pct = discount_fraction * 100  # e.g. Decimal('10.0') for 10%

    out = ["Customer: %s" % customer_name]
    tax_lines = []
    subtotal_cents = 0

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: %s" % sku)
            continue

        unit_cents = _to_cents(item["price"])
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        tax_lines.append({"category": item["category"], "amount_cents": amount_cents})
        out.append("%s x%d @ %s = %s" % (sku, qty, _money(unit_cents), _money(amount_cents)))

    # Discount = subtotal * discount rate, rounded to the cent (half up).
    discount_cents = int(
        (Decimal(subtotal_cents) * discount_fraction).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    result = tax.compute_tax(
        lines=tax_lines,
        region=region,
        discount_pct=float(discount_pct),
    )
    tax_cents = result["tax_cents"]
    tax_pct = result["tax_pct"]

    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: %s" % _money(subtotal_cents))
    out.append("Discount (%s%%): -%s" % (_percent(discount_pct), _money(discount_cents)))
    out.append("Tax (%s%%): %s" % (_percent(tax_pct), _money(tax_cents)))
    out.append("Total: %s" % _money(total_cents))

    return "\n".join(out)
