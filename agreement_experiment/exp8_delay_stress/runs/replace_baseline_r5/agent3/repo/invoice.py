"""Invoice module. Owned by agent3. Implement render_invoice(order).

Agreed interfaces (see agreement log):
  pricing.get_item(sku)          -> Item(sku, name, price, category) or None
                                    price is float dollars
  pricing.get_customer(cid)      -> Customer(id, name, discount, region) or None
                                    discount is a fraction (0.10 = 10% off)
  tax.compute_tax(lines, region, discount_pct=0) -> int cents
                                    lines = [(category, amount_cents), ...]
                                    discount_pct is a percent number (10 = 10%)
  tax.rate_pct(region)           -> percent number (8.25 for TX)

Invoice money is handled as Decimal dollars internally; cents are used at
the boundary with tax.py. This module does not decide tax rules itself.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _cents_from_dollars(value):
    """Convert a dollar amount (float, str, or Decimal) to integer cents, half up."""
    d = Decimal(str(value)) * 100
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format integer cents as a dollar string without sign, e.g. 2500 -> '$25.00'."""
    return "${:.2f}".format(Decimal(cents) / 100)


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0.0 -> '0'."""
    d = Decimal(str(value)).normalize()
    return format(d, "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_name = customer.name
        discount_fraction = Decimal(str(customer.discount))
        region = customer.region

    # Build the lines. Unknown skus keep their position as a text line and are skipped
    # in all money computations.
    output_lines = ["Customer: " + customer_name]
    taxable_lines = []  # (category, amount_cents) for tax.py
    subtotal_cents = 0

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output_lines.append("UNKNOWN SKU: " + str(sku))
            continue
        unit_cents = _cents_from_dollars(item.price)
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        output_lines.append(
            "{} x{} @ {} = {}".format(sku, qty, _money(unit_cents), _money(amount_cents))
        )
        taxable_lines.append((item.category, amount_cents))

    # Discount = subtotal * discount fraction, rounded to the cent (half up).
    discount_cents = int(
        (Decimal(subtotal_cents) * discount_fraction).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    # Tax is computed entirely by tax.py. discount_pct is a percent number.
    discount_pct = discount_fraction * 100
    tax_cents = tax.compute_tax(taxable_lines, region, float(discount_pct))
    tax_pct = 0 if region is None else tax.rate_pct(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    output_lines.append("Subtotal: " + _money(subtotal_cents))
    output_lines.append(
        "Discount ({}%): -{}".format(_percent(discount_pct), _money(discount_cents))
    )
    output_lines.append("Tax ({}%): {}".format(_percent(tax_pct), _money(tax_cents)))
    output_lines.append("Total: " + _money(total_cents))

    return "\n".join(output_lines)
