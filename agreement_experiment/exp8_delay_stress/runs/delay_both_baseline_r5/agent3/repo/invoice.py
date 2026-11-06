"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the agreed APIs (shared agreement log, topics pricing_api and tax_api):
  pricing.get_item(sku) -> {sku, name, unit_price (float dollars), category} or None
  pricing.get_customer(cid) -> {id, name, discount (fraction, 0.10 = 10%), region} or None
  tax.tax_rate_pct(region) -> float percent (8.25 = 8.25%); None -> 0
  tax.sales_tax_cents(lines, region, discount_pct) -> int cents
      lines = [(category, amount_cents)], discount_pct = customer's percent (10 = 10%)

Money is handled as decimal.Decimal dollars internally; floats/ints from the
other modules are converted at this boundary. This module does not compute
any tax rules itself.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ZERO = Decimal("0")
HUNDRED = Decimal("100")


def _cents(amount):
    """Round a Decimal amount to the cent, half up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal amount as $12.50 (the sign is handled by the caller)."""
    return "$" + format(_cents(abs(amount)), ".2f")


def _percent(value):
    """Format a percent without trailing zeros: 10, 8.25, 0."""
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text if text else "0"


def render_invoice(order):
    customer = pricing.get_customer(order["customer"])
    if customer is None:
        # Unknown customer: shown by id, 0% discount, no region -> 0% tax.
        customer_label = order["customer"]
        discount_fraction = ZERO
        region = None
    else:
        customer_label = customer["name"] or order["customer"]
        discount_fraction = Decimal(str(customer["discount"]))
        region = customer["region"]

    output = ["Customer: " + customer_label]

    subtotal = ZERO
    tax_lines = []  # (category, amount_cents) for known skus only
    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output.append("UNKNOWN SKU: " + sku)
            continue
        unit = Decimal(str(item["unit_price"]))
        amount = _cents(unit * quantity)
        subtotal += amount
        tax_lines.append((item["category"], int(amount * 100)))
        output.append(
            "{} x{} @ {} = {}".format(sku, quantity, _money(unit), _money(amount))
        )

    # Discount: subtotal * discount fraction, rounded to the cent (half up).
    discount = _cents(subtotal * discount_fraction)
    discount_pct = discount_fraction * HUNDRED

    # Tax amount and rate come from tax.py.
    tax_amount = Decimal(tax.sales_tax_cents(tax_lines, region, discount_pct)) / HUNDRED
    tax_pct = Decimal(str(tax.tax_rate_pct(region)))

    total = _cents(subtotal - discount + tax_amount)

    output.append("Subtotal: " + _money(subtotal))
    output.append("Discount ({}%): -{}".format(_percent(discount_pct), _money(discount)))
    output.append("Tax ({}%): {}".format(_percent(tax_pct), _money(tax_amount)))
    output.append("Total: " + _money(total))

    return "\n".join(output)
