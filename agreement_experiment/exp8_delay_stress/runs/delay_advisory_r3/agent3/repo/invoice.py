"""Invoice module. Owned by agent3.

render_invoice(order) builds the text of one invoice. All item, customer and
tax information comes from pricing.py and tax.py (committed decisions
pricing_api v2, pricing_missing v1, TAX_API v3, TAX_UNKNOWN_REGION v1).
This module computes no tax rules itself.

Arithmetic is done in integer cents (exact); money is shown as dollars.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as dollars, e.g. 1250 -> '$12.50', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "{}${}.{:02d}".format(sign, cents // 100, cents % 100)


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros.

    0.10 -> '10', 0.0825 -> '8.25', 0 -> '0'.
    """
    value = (Decimal(str(fraction)) * 100).normalize()
    return format(value, "f")


def _discount_cents(subtotal_cents, discount_fraction):
    """subtotal * discount, rounded to the cent (half up)."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_fraction))
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    """Return the invoice text for order = {"customer": id, "lines": [[sku, qty], ...]}."""
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None -> tax 0).
        customer_name = customer_id
        discount_fraction = 0.0
        region = None
    else:
        customer_name = customer["name"] or customer_id
        discount_fraction = customer["discount"]
        region = customer["region"]

    out = ["Customer: {}".format(customer_name)]
    taxable_lines = []  # {"category", "amount_cents"} for known skus only
    subtotal_cents = 0

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: {}".format(sku))
            continue
        unit_cents = item["price_cents"]
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        taxable_lines.append({"category": item["category"], "amount_cents": amount_cents})
        out.append("{} x{} @ {} = {}".format(sku, qty, _money(unit_cents), _money(amount_cents)))

    discount_cents = _discount_cents(subtotal_cents, discount_fraction)
    tax_cents = tax.compute_tax(taxable_lines, region, discount_fraction)
    tax_rate = tax.rate(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: {}".format(_money(subtotal_cents)))
    out.append("Discount ({}%): -{}".format(_percent(discount_fraction), _money(discount_cents)))
    out.append("Tax ({}%): {}".format(_percent(tax_rate), _money(tax_cents)))
    out.append("Total: {}".format(_money(total_cents)))

    return "\n".join(out)
