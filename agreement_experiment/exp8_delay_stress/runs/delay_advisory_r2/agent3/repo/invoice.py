"""Invoice module. Owned by agent3. Implements render_invoice(order).

Committed interfaces used (see the shared decision log):
  PRICING_API v2:   pricing.get_item(sku) -> dict | None   (keys: sku, name, price_cents, category)
                    pricing.get_customer(cid) -> dict | None (keys: id, name, discount, region)
                    discount is a fraction (0.10 = 10%); all money is int cents.
  TAX_API v2:       tax.compute_tax(region, lines, discount) -> int cents
                    lines = [{"category": str, "amount_cents": int}, ...] for all known line items.
  TAX_RATE v1:      tax.tax_rate(region) -> float fraction (0.0825 = 8.25%)
  UNKNOWN_CUSTOMER_TAX v1: region None (unknown customer) -> tax 0 and rate 0.0.

This module does no tax rule computation. It only does arithmetic on subtotal,
discount and total, and formats the output.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format a non-negative integer cent amount as '$12.50'."""
    return "${}.{:02d}".format(cents // 100, cents % 100)


def _percent(fraction):
    """Format a fraction as a percent with no trailing zeros: 0.1 -> '10', 0.0825 -> '8.25'."""
    value = (Decimal(str(fraction)) * 100).normalize()
    return format(value, "f")


def render_invoice(order):
    """Return the invoice text for an order.

    order: {"customer": "C1", "lines": [["A", 2], ["D", 2], ["Z", 1]]}  (sku, quantity)
    """
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (UNKNOWN_CUSTOMER_TAX).
        customer_name = customer_id
        discount_fraction = 0.0
        region = None
    else:
        customer_name = customer["name"]
        discount_fraction = customer["discount"]
        region = customer["region"]

    out_lines = ["Customer: {}".format(customer_name)]
    taxable_lines = []  # known line items only, as TAX_API expects
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: {}".format(sku))
            continue
        unit_cents = item["price_cents"]
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        taxable_lines.append({"category": item["category"], "amount_cents": amount_cents})
        out_lines.append("{} x{} @ {} = {}".format(
            sku, quantity, _money(unit_cents), _money(amount_cents)))

    # Discount = subtotal * discount fraction, rounded to the cent (half up).
    discount_cents = int(
        (Decimal(subtotal_cents) * Decimal(str(discount_fraction)))
        .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    tax_cents = tax.compute_tax(region, taxable_lines, discount_fraction)
    tax_rate = tax.tax_rate(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append("Subtotal: {}".format(_money(subtotal_cents)))
    out_lines.append("Discount ({}%): -{}".format(_percent(discount_fraction), _money(discount_cents)))
    out_lines.append("Tax ({}%): {}".format(_percent(tax_rate), _money(tax_cents)))
    out_lines.append("Total: {}".format(_money(total_cents)))

    return "\n".join(out_lines)
