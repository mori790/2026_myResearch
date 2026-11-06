"""Invoice module. Owned by agent3. Implement render_invoice(order).

Depends on:
  pricing.get_item(sku)           -> Item (sku, name, price [float dollars], category) or None
  pricing.get_customer(cid)       -> Customer (customer_id, name, discount [fraction], region) or None
  tax.calculate_tax(lines, region, discount_pct) -> int cents
  tax.tax_rate_pct(region)        -> Decimal percent (e.g. Decimal('8.25'))

Money is handled as Decimal internally; tax.py works in integer cents.
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def _to_decimal(value):
    """Convert a float/int/str amount to Decimal without float noise (12.5 -> Decimal('12.5'))."""
    return Decimal(str(value))


def _round_half_up(value):
    """Round a Decimal to an integer, half up."""
    return int(value.quantize(ONE, rounding=ROUND_HALF_UP))


def _to_cents(amount):
    """Decimal dollars -> integer cents, rounded half up."""
    return _round_half_up(amount * HUNDRED)


def _cents_to_decimal(cents):
    """Integer cents -> Decimal dollars (exact)."""
    return Decimal(cents) / HUNDRED


def _money(amount):
    """Decimal dollars -> text with exactly two decimals, e.g. Decimal('12.5') -> '12.50'."""
    return str(amount.quantize(CENT, rounding=ROUND_HALF_UP))


def _percent_text(percent):
    """Decimal percent -> text without trailing zeros, e.g. Decimal('10.00') -> '10', Decimal('8.25') -> '8.25'."""
    return format(percent.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    output = []
    known_lines = []  # (category, amount_cents) for tax.py; unknown SKUs are excluded
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = _to_cents(_to_decimal(item.price))
        line_cents = unit_cents * quantity
        subtotal_cents += line_cents
        known_lines.append((item.category, line_cents))
        output.append(
            f"{sku} x{quantity} @ ${_money(_cents_to_decimal(unit_cents))}"
            f" = ${_money(_cents_to_decimal(line_cents))}"
        )

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_fraction = Decimal("0")
        discount_percent = Decimal("0")
        tax_cents = 0
        tax_percent = Decimal("0")
    else:
        customer_name = customer.name or customer_id
        discount_fraction = _to_decimal(customer.discount)
        discount_percent = discount_fraction * HUNDRED
        # tax.py takes the discount as a whole percent when it is whole (10 -> 10).
        discount_pct_arg = (
            int(discount_percent)
            if discount_percent == discount_percent.to_integral_value()
            else discount_percent
        )
        tax_cents = int(tax.calculate_tax(known_lines, customer.region, discount_pct_arg))
        tax_percent = tax.tax_rate_pct(customer.region)

    discount_cents = _round_half_up(Decimal(subtotal_cents) * discount_fraction)
    total_cents = subtotal_cents - discount_cents + tax_cents

    header = [f"Customer: {customer_name}"]
    footer = [
        f"Subtotal: ${_money(_cents_to_decimal(subtotal_cents))}",
        f"Discount ({_percent_text(discount_percent)}%): -${_money(_cents_to_decimal(discount_cents))}",
        f"Tax ({_percent_text(tax_percent)}%): ${_money(_cents_to_decimal(tax_cents))}",
        f"Total: ${_money(_cents_to_decimal(total_cents))}",
    ]
    return "\n".join(header + output + footer)
