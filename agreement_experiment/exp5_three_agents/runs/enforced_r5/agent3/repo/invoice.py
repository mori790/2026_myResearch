"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed APIs:
  pricing.get_item(sku)           -> Item(sku, name, price_cents, category); KeyError subclass if unknown
  pricing.get_customer(cid)       -> Customer(id, name, discount_percent, region); KeyError subclass if unknown
  tax.calculate_tax(lines, region, discount_pct) -> int cents
  tax.tax_rate_percent(region)    -> Decimal percent (0 if unknown)

All money crosses module boundaries as integer cents. Decimal is used only for
percent arithmetic and formatting. Tax rules are not computed here.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format non-negative integer cents as $X.YY."""
    cents = abs(int(cents))
    return "$%d.%02d" % (cents // 100, cents % 100)


def _percent(value):
    """Format a percent without trailing zeros (10 -> '10', 8.25 -> '8.25', 0 -> '0')."""
    d = Decimal(value)
    return format(d.normalize(), "f")


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * pct / 100, rounded to the cent, half up."""
    exact = Decimal(subtotal_cents) * Decimal(discount_pct) / Decimal(100)
    return int(exact.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def render_invoice(order):
    # Customer: unknown ids are shown by id, with 0% discount and no region (0% tax).
    customer_id = order["customer"]
    try:
        customer = pricing.get_customer(customer_id)
        customer_name = customer.name
        discount_pct = customer.discount_percent
        region = customer.region
    except KeyError:
        customer_name = customer_id
        discount_pct = 0
        region = None

    out = ["Customer: %s" % customer_name]

    # Lines: unknown SKUs are listed in place and skipped in the totals.
    taxable_lines = []
    subtotal_cents = 0
    for sku, qty in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            out.append("UNKNOWN SKU: %s" % sku)
            continue
        line_cents = item.price_cents * qty
        subtotal_cents += line_cents
        taxable_lines.append((item.category, line_cents))
        out.append("%s x%d @ %s = %s" % (
            sku, qty, _money(item.price_cents), _money(line_cents)))

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    tax_cents = tax.calculate_tax(taxable_lines, region, discount_pct)
    tax_percent = tax.tax_rate_percent(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: %s" % _money(subtotal_cents))
    out.append("Discount (%s%%): -%s" % (_percent(discount_pct), _money(discount_cents)))
    out.append("Tax (%s%%): %s" % (_percent(tax_percent), _money(tax_cents)))
    out.append("Total: %s" % _money(total_cents))

    return "\n".join(out)
