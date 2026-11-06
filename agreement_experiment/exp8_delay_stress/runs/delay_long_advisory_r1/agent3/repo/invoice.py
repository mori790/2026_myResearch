"""Invoice module. Owned by agent3. Implement render_invoice(order).

Decisions used (committed in the shared log):
  PRICING_API v2: pricing.get_item(sku) -> {sku, name, price_cents, category}, KeyError if unknown
                  pricing.get_customer(id) -> {id, name, discount_pct, region}, KeyError if unknown
  tax_api v1:     tax.compute_sales_tax(lines, region, discount_pct) -> int cents
                  tax.tax_rate_pct(region) -> float percent (None -> 0)

This module does no tax computation itself. Money is handled as integer cents
internally and formatted as dollars at the end.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format a non-negative integer number of cents as '$12.50'."""
    return "${}.{:02d}".format(cents // 100, cents % 100)


def _pct(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * discount_pct / 100, rounded to the cent (half up)."""
    amount = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]

    # Customer lookup. An unknown customer is shown by its id, with 0% discount and 0% tax.
    try:
        customer = pricing.get_customer(customer_id)
        customer_name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]
    except KeyError:
        customer_name = customer_id
        discount_pct = 0
        region = None

    out = ["Customer: {}".format(customer_name)]

    # Line items. Unknown skus are shown in place and left out of the totals.
    taxable_lines = []  # what tax.py needs: category and line amount in cents
    subtotal_cents = 0
    for sku, qty in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            out.append("UNKNOWN SKU: {}".format(sku))
            continue
        amount_cents = item["price_cents"] * qty
        subtotal_cents += amount_cents
        taxable_lines.append({"category": item["category"], "amount_cents": amount_cents})
        out.append("{} x{} @ {} = {}".format(sku, qty, _money(item["price_cents"]), _money(amount_cents)))

    # Discount: computed on the subtotal, rounded to the cent.
    discount_cents = _discount_cents(subtotal_cents, discount_pct)

    # Tax: computed by tax.py. It applies the discount to the taxable lines itself.
    tax_cents = tax.compute_sales_tax(taxable_lines, region, discount_pct)
    tax_pct = tax.tax_rate_pct(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: {}".format(_money(subtotal_cents)))
    out.append("Discount ({}%): -{}".format(_pct(discount_pct), _money(discount_cents)))
    out.append("Tax ({}%): {}".format(_pct(tax_pct), _money(tax_cents)))
    out.append("Total: {}".format(_money(total_cents)))

    return "\n".join(out)
