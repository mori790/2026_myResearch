"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed APIs (agree log: pricing_api v1, tax.interface v2):
  pricing.get_item(sku) -> dict | None              (price: float dollars, category: str)
  pricing.get_customer(customer_id) -> dict | None  (name, discount: float fraction, region: str)
  tax.sales_tax(lines, region, discount_pct) -> int cents
  tax.tax_rate(region) -> float percent

Money is computed in integer cents (converted from the float dollars at this boundary).
Tax rules are NOT computed here; they come from tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(dollars):
    """Convert a dollar amount (float, int, str or Decimal) to integer cents, rounded half up."""
    value = Decimal(repr(dollars)) if isinstance(dollars, float) else Decimal(str(dollars))
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format non-negative integer cents as $X.YY."""
    return "$%d.%02d" % (cents // 100, cents % 100)


def _percent(value):
    """Format a percent number without trailing zeros (10, 8.25, 0)."""
    d = Decimal(repr(value)) if isinstance(value, float) else Decimal(str(value))
    text = format(d.normalize(), "f")
    if text in ("-0", "-0.0"):
        text = "0"
    return text


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None -> tax 0).
        customer_name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_name = customer["name"]
        discount_fraction = Decimal(repr(customer["discount"])) if isinstance(customer["discount"], float) \
            else Decimal(str(customer["discount"]))
        region = customer["region"]

    discount_pct = discount_fraction * 100  # percent number, e.g. 10 for 10%

    out_lines = ["Customer: %s" % customer_name]
    tax_lines = []
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: %s" % sku)
            continue

        unit_cents = _to_cents(item["price"])
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        tax_lines.append({"category": item["category"], "amount_cents": amount_cents})
        out_lines.append("%s x%d @ %s = %s" % (sku, quantity, _money(unit_cents), _money(amount_cents)))

    # Discount = subtotal * discount fraction, rounded to the cent (half up), in integer cents.
    discount_cents = int((Decimal(subtotal_cents) * discount_fraction).quantize(Decimal("1"),
                                                                              rounding=ROUND_HALF_UP))

    tax_cents = tax.sales_tax(tax_lines, region, discount_pct)
    tax_percent = tax.tax_rate(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append("Subtotal: %s" % _money(subtotal_cents))
    out_lines.append("Discount (%s%%): -%s" % (_percent(discount_pct), _money(discount_cents)))
    out_lines.append("Tax (%s%%): %s" % (_percent(tax_percent), _money(tax_cents)))
    out_lines.append("Total: %s" % _money(total_cents))

    return "\n".join(out_lines)
