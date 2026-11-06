"""Invoice module. Owned by agent3. Implements render_invoice(order).

Uses:
  pricing.get_item(sku)          -> Item or None   (Item.sku, name, price float dollars, category)
  pricing.get_customer(id)       -> Customer or None (Customer.id, name, discount fraction e.g. 0.10, region)
  tax.compute_tax_details(lines, region, discount_pct) -> TaxResult
      lines: (category, amount_cents) tuples, pre-discount, all lines
      region: customer region, or None for unknown customer (0% tax)
      discount_pct: percent number, e.g. 10
      TaxResult: taxable_cents, tax_pct (percent number), tax_cents

Money is kept in int cents internally. Discount is computed here (subtotal * discount, rounded half up
to the cent); the tax module computes tax from its own rules.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(amount):
    """Convert a dollar amount (float, int, str or Decimal) to int cents, rounding half up."""
    value = (Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(value)


def _fmt_money(cents):
    """Format int cents as $X.XX."""
    return "$%d.%02d" % (cents // 100, cents % 100)


def _fmt_percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    d = Decimal(str(value)).normalize()
    return format(d, "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_label = customer_id
        region = None
        discount_fraction = Decimal("0")
    else:
        customer_label = customer.name or customer_id
        region = customer.region
        discount_fraction = Decimal(str(customer.discount))

    output = ["Customer: %s" % customer_label]

    subtotal_cents = 0
    taxable_lines = []  # (category, amount_cents) for known SKUs only
    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output.append("UNKNOWN SKU: %s" % sku)
            continue
        unit_cents = _to_cents(item.price)
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        taxable_lines.append((item.category, amount_cents))
        output.append("%s x%d @ %s = %s" % (
            sku, quantity, _fmt_money(unit_cents), _fmt_money(amount_cents)))

    discount_cents = int((Decimal(subtotal_cents) * discount_fraction)
                         .quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    discount_pct = discount_fraction * 100

    result = tax.compute_tax_details(taxable_lines, region, float(discount_pct))
    tax_cents = int(result.tax_cents)
    tax_pct = result.tax_pct

    total_cents = subtotal_cents - discount_cents + tax_cents

    output.append("Subtotal: %s" % _fmt_money(subtotal_cents))
    output.append("Discount (%s%%): -%s" % (_fmt_percent(discount_pct), _fmt_money(discount_cents)))
    output.append("Tax (%s%%): %s" % (_fmt_percent(tax_pct), _fmt_money(tax_cents)))
    output.append("Total: %s" % _fmt_money(total_cents))

    return "\n".join(output)
