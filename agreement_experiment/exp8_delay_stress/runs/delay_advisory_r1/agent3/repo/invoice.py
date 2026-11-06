"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed decisions:
  pricing_api v2:
    pricing.get_item(sku)           -> {"sku", "name", "price_cents": int, "category"} or None
    pricing.get_customer(cust_id)   -> {"id", "name", "discount_pct": number, "region"} or None
  TAX_API v1:
    tax.compute_tax(region, lines, discount_pct) -> int cents (tax amount only)
    tax.tax_rate_pct(region)                    -> Decimal percent (e.g. Decimal("8.25"))
  TAX_UNKNOWN_CUSTOMER v1:
    region None -> 0% tax, no error

Team standard inside this module: money is Decimal dollars, percents are
percent numbers converted to multipliers where needed. Money is rounded to the
cent with ROUND_HALF_UP.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_decimal(value):
    """Convert an int, float or Decimal from another module to an exact Decimal."""
    return Decimal(str(value))


def _money(amount):
    """Format a Decimal dollar amount with two decimals, e.g. Decimal('25') -> '25.00'."""
    return format(amount.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(_to_decimal(value).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (TAX_UNKNOWN_CUSTOMER).
        customer_name = customer_id
        discount_pct = Decimal("0")
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = _to_decimal(customer["discount_pct"])
        region = customer["region"]

    output = [f"Customer: {customer_name}"]

    # Pass 1: price every line. Unknown SKUs are listed in place and skipped.
    priced_lines = []  # (category, amount_cents) for known SKUs, in order
    subtotal = Decimal("0")
    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = int(item["price_cents"])
        amount_cents = unit_cents * quantity
        unit_price = Decimal(unit_cents) / 100
        amount = Decimal(amount_cents) / 100
        subtotal += amount
        priced_lines.append([item["category"], amount_cents])
        output.append(f"{sku} x{quantity} @ ${_money(unit_price)} = ${_money(amount)}")

    # Discount: subtotal * discount percent, rounded to the cent (half up).
    discount = (subtotal * discount_pct / 100).quantize(CENT, rounding=ROUND_HALF_UP)

    # Tax is computed entirely by tax.py (TAX_API). Integer cents in and out.
    tax_amount = Decimal(tax.compute_tax(region, priced_lines, float(discount_pct))) / 100
    tax_rate = _to_decimal(tax.tax_rate_pct(region))

    total = subtotal - discount + tax_amount

    output.append(f"Subtotal: ${_money(subtotal)}")
    output.append(f"Discount ({_percent(discount_pct)}%): -${_money(discount)}")
    output.append(f"Tax ({_percent(tax_rate)}%): ${_money(tax_amount)}")
    output.append(f"Total: ${_money(total)}")

    return "\n".join(output)
