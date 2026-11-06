"""Invoice module. Owned by agent3. Implement render_invoice(order).

Division of responsibilities (agreed in the agreement log, topics tax_api):
- pricing.py supplies item prices/categories and customer name, discount and region.
- tax.py supplies every tax rule: compute_tax(lines, region, discount_pct) -> int cents,
  and tax_rate_pct(region) -> Decimal percent.
- This module only does the arithmetic and formatting. It contains no tax rules.

Internal representation: money is integer cents (no float rounding), percentages are
Decimal. pricing.py returns floats/fractions, so values are converted at the boundary.
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(amount):
    """Convert a dollar amount (float, int, str or Decimal) to integer cents, half up."""
    value = Decimal(str(amount)) * 100
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format integer cents as dollars, e.g. 1250 -> '$12.50', 0 -> '$0.00'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "{}${}.{:02d}".format(sign, cents // 100, cents % 100)


def _percent(value):
    """Format a Decimal percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(value).normalize(), "f")


def _customer_info(cust_id):
    """Return (display_name, discount_pct, region) for a customer id.

    Unknown customers are shown by id, with 0% discount and no region (so no tax).
    """
    customer = pricing.get_customer(cust_id)
    if customer is None:
        return cust_id, Decimal(0), None
    # pricing.py gives the discount as a fraction (0.10); tax.py wants a percent (10).
    discount_pct = Decimal(str(customer.discount)) * 100
    return customer.name, discount_pct, customer.region


def render_invoice(order):
    customer_id = order["customer"]
    name, discount_pct, region = _customer_info(customer_id)

    out = ["Customer: {}".format(name)]
    subtotal_cents = 0
    taxable_lines = []  # (amount_cents, category) for every known line, as tax.py expects

    for sku, quantity in order["lines"]:
        unit_price = pricing.item_price(sku)
        if unit_price is None:
            out.append("UNKNOWN SKU: {}".format(sku))
            continue
        unit_cents = _to_cents(unit_price)
        line_cents = unit_cents * quantity
        subtotal_cents += line_cents
        category = pricing.item_category(sku)
        taxable_lines.append((line_cents, category))
        out.append("{} x{} @ {} = {}".format(sku, quantity, _money(unit_cents), _money(line_cents)))

    # discount = subtotal * discount percent, rounded to the cent (half up)
    discount_cents = int(
        (Decimal(subtotal_cents) * discount_pct / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    tax_cents = tax.compute_tax(taxable_lines, region, discount_pct)
    tax_pct = tax.tax_rate_pct(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: {}".format(_money(subtotal_cents)))
    out.append("Discount ({}%): -{}".format(_percent(discount_pct), _money(discount_cents)))
    out.append("Tax ({}%): {}".format(_percent(tax_pct), _money(tax_cents)))
    out.append("Total: {}".format(_money(total_cents)))

    return "\n".join(out)
