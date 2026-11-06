"""Invoice module. Owned by agent3.

Implements render_invoice(order). All item, customer and tax data come from
pricing.py and tax.py; this module never applies tax rules itself.

Committed decisions used here:
  MONEY_UNIT   float dollars (12.5 means $12.50)
  PERCENT_UNIT fraction (0.10 means 10%)
  LOOKUP_MISS  lookups return None when nothing is found
  PRICING_API  unit_price(sku), item_category(sku), customer(cid)
  tax.api      compute_tax(lines, region, discount) -> float dollars,
               rate(region) -> fraction or None
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dec(value):
    """Convert a float dollar amount to an exact-ish Decimal via its shortest repr."""
    return Decimal(repr(float(value)))


def _to_cents(value):
    """Round a Decimal (or float) to the cent, half up."""
    return _dec(value).quantize(CENT, rounding=ROUND_HALF_UP) if isinstance(value, float) \
        else value.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(value):
    """Format a Decimal dollar amount as '$12.50' (negative values get a leading '-')."""
    cents = _to_cents(value)
    sign = "-" if cents < 0 else ""
    return f"{sign}${abs(cents):.2f}"


def _percent(fraction):
    """Format a fraction as a percent string without trailing zeros: 0.0825 -> '8.25%'."""
    if fraction is None:
        fraction = 0.0
    pct = _dec(fraction).scaleb(2)
    text = format(pct.normalize(), "f")
    return f"{text}%"


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (tax.py handles region None).
        name = customer_id
        region = None
        discount = 0.0
    else:
        name = customer["name"]
        region = customer["region"]
        discount = customer["discount"]

    out_lines = [f"Customer: {name}"]
    priced = []        # (sku, quantity, unit_price_dec, line_amount_dec, category)
    subtotal = Decimal("0")

    for sku, quantity in order["lines"]:
        unit = pricing.unit_price(sku)
        if unit is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_dec = _dec(unit)
        amount_dec = unit_dec * quantity
        subtotal += amount_dec
        category = pricing.item_category(sku)
        priced.append((sku, quantity, unit_dec, amount_dec, category))
        out_lines.append(f"{sku} x{quantity} @ {_money(unit_dec)} = {_money(amount_dec)}")

    subtotal = _to_cents(subtotal)
    discount_amount = _to_cents(subtotal * _dec(discount))

    # tax.py applies the discount to the taxable base itself, so pass undiscounted amounts.
    tax_lines = [
        {"amount": float(amount_dec), "category": category}
        for (_sku, _qty, _unit, amount_dec, category) in priced
    ]
    tax_amount = _to_cents(_dec(tax.compute_tax(tax_lines, region, discount)))
    tax_rate = tax.rate(region)

    total = subtotal - discount_amount + tax_amount

    out_lines.append(f"Subtotal: {_money(subtotal)}")
    out_lines.append(f"Discount ({_percent(discount)}): -{_money(discount_amount)}")
    out_lines.append(f"Tax ({_percent(tax_rate)}): {_money(tax_amount)}")
    out_lines.append(f"Total: {_money(total)}")

    return "\n".join(out_lines)
