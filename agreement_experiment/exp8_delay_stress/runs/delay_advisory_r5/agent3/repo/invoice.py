"""Invoice module. Owned by agent3.

render_invoice(order) builds the plain-text invoice. All item, customer and
tax information comes from pricing.py and tax.py (committed decisions
pricing_api, TAX_API v2, TAX_UNKNOWN v1). This module never applies tax rules.

Conventions (committed decisions):
- pricing.py returns price as float dollars and discount as a fraction (0.10 = 10%).
  Converted here to Decimal via str() to avoid float artifacts.
- compute_tax(lines, region, discount_pct) takes int cents per line and a percent
  number, and returns int cents.
- tax_percent(region) returns the rate as a percent number (e.g. 8.25).
- region None means an unknown customer: tax is 0.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def _to_decimal(value):
    """Convert a number from another module (float, int, str) to Decimal."""
    return Decimal(str(value))


def _round_cents(amount):
    """Round a Decimal dollar amount to the cent, half up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal dollar amount as $12.50 (a negative value as -$3.91)."""
    q = _round_cents(amount)
    if q == 0:
        q = Decimal("0.00")  # avoid printing "-0.00"
    if q < 0:
        return "-$" + format(-q, "f")
    return "$" + format(q, "f")


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10%', 8.25 -> '8.25%', 0 -> '0%'."""
    return format(_to_decimal(value).normalize(), "f") + "%"


def render_invoice(order):
    """Return the invoice text for an order.

    order = {"customer": "C1", "lines": [["A", 2], ["D", 2], ["Z", 1]]}
    where each line is (sku, quantity).
    """
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None -> tax 0).
        customer_name = customer_id
        discount_pct = Decimal("0")
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = _to_decimal(customer["discount"]) * HUNDRED  # 0.10 -> 10
        region = customer["region"]

    out_lines = ["Customer: " + str(customer_name)]
    subtotal = Decimal("0")
    tax_lines = []  # (category, amount_cents) for tax.compute_tax

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: " + str(sku))
            continue
        unit_price = _to_decimal(item["price"])
        quantity = _to_decimal(qty)
        amount = unit_price * quantity
        subtotal += amount
        out_lines.append(
            "{} x{} @ {} = {}".format(sku, qty, _money(unit_price), _money(amount))
        )
        amount_cents = int((amount * HUNDRED).quantize(ONE, rounding=ROUND_HALF_UP))
        tax_lines.append((item["category"], amount_cents))

    # Discount is computed here, rounded to the cent (half up).
    discount = _round_cents(subtotal * discount_pct / HUNDRED)

    # Tax amount and rate come from tax.py only.
    tax_cents = tax.compute_tax(tax_lines, region, float(discount_pct))
    tax_amount = Decimal(tax_cents) / HUNDRED
    tax_pct = tax.tax_percent(region)

    total = subtotal - discount + tax_amount

    out_lines.append("Subtotal: " + _money(subtotal))
    out_lines.append("Discount ({}): -{}".format(_percent(discount_pct), _money(discount)))
    out_lines.append("Tax ({}): {}".format(_percent(tax_pct), _money(tax_amount)))
    out_lines.append("Total: " + _money(total))

    return "\n".join(out_lines)
