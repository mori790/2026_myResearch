"""Invoice module. Owned by agent3. Implement render_invoice(order).

Conventions (team standard):
- Money amounts are decimal.Decimal in dollars.
- Percentages are multipliers (10% off is 0.90; 8.25% tax is 1.0825).
- A lookup that finds nothing returns a default value.

Module APIs used:
- pricing (agreed topic 'invoice_pricing_api'):
    sku_exists(sku) -> bool
    unit_price(sku) -> Decimal dollars (Decimal(0) if unknown)
    category(sku) -> str ('' if unknown)
    customer_name(customer_id) -> str ('' if unknown)
    customer_region(customer_id) -> str region code ('' if unknown customer)
    customer_discount(customer_id) -> Decimal multiplier (Decimal(1) if unknown)
- tax (agent2's implemented API, adopted):
    sales_tax_cents(region, lines, discount_pct=0) -> int cents
        region: region code, or None for an unknown customer (0% tax)
        lines: iterable of (category, amount_cents), one pair per item
        discount_pct: customer discount as a percent number (10 for 10%)
    tax_pct_for_region(region) -> Decimal percent (for display)

Tax rules are NOT implemented here; invoice.py only converts units at the
boundary (Decimal dollars <-> int cents, multiplier <-> percent).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def _quantize(amount):
    """Round a Decimal dollar amount to the cent, half up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _to_cents(amount):
    """Convert a Decimal dollar amount (already at cent precision) to int cents."""
    return int(_quantize(amount) * 100)


def _from_cents(cents):
    """Convert int cents to a Decimal dollar amount."""
    return _quantize(Decimal(cents) / HUNDRED)


def _money(amount):
    """Format a Decimal dollar amount as e.g. '$12.50' (negative: '-$3.91')."""
    amount = _quantize(amount)
    if amount < 0:
        return "-$" + format(-amount, "f")
    return "$" + format(amount, "f")


def _percent(value):
    """Format a percent Decimal without trailing zeros, e.g. '10', '8.25', '0'."""
    text = format(Decimal(value).normalize(), "f")
    if text in ("-0", ""):
        text = "0"
    return text


def render_invoice(order):
    customer_id = order["customer"]
    customer_name = pricing.customer_name(customer_id) or customer_id
    region = pricing.customer_region(customer_id) or None  # None = unknown customer
    discount_multiplier = pricing.customer_discount(customer_id)
    discount_pct = (ONE - discount_multiplier) * HUNDRED

    lines_out = ["Customer: " + customer_name]

    subtotal = Decimal("0")
    tax_lines = []
    for sku, quantity in order["lines"]:
        if not pricing.sku_exists(sku):
            lines_out.append("UNKNOWN SKU: " + sku)
            continue
        unit_price = pricing.unit_price(sku)
        line_amount = _quantize(unit_price * quantity)
        subtotal += line_amount
        tax_lines.append((pricing.category(sku), _to_cents(line_amount)))
        lines_out.append(
            "{} x{} @ {} = {}".format(sku, quantity, _money(unit_price), _money(line_amount))
        )

    subtotal = _quantize(subtotal)
    discount = _quantize(subtotal * (ONE - discount_multiplier))

    tax_cents = tax.sales_tax_cents(region, tax_lines, discount_pct)
    tax_amount = _from_cents(tax_cents)
    tax_percent = _percent(tax.tax_pct_for_region(region))

    total = _quantize(subtotal - discount + tax_amount)

    lines_out.append("Subtotal: " + _money(subtotal))
    lines_out.append("Discount ({}%): -{}".format(_percent(discount_pct), _money(discount)))
    lines_out.append("Tax ({}%): {}".format(tax_percent, _money(tax_amount)))
    lines_out.append("Total: " + _money(total))

    return "\n".join(lines_out)
