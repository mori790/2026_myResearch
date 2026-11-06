"""Invoice module. Owned by agent3. Implement render_invoice(order).

Interfaces used (agreed in the team log):
  pricing.get_item(sku)          -> Item(sku, name, price, category) or None
                                    (price: float dollars)
  pricing.get_customer(cust_id)  -> Customer(id, name, discount, region) or None
  pricing.get_discount(cust_id)  -> fraction (0.10 = 10%) or None
  tax.compute_tax(lines, region, discount_pct) -> int cents
                                    lines: [{"category": str, "amount_cents": int}]
  tax.tax_pct_for_region(region) -> Decimal percent (KeyError if unknown)

Internally money is Decimal dollars; conversion to cents / percent numbers
happens only at the boundary with pricing.py and tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _to_decimal(value):
    """Convert a float/int/str from another module to Decimal without binary noise."""
    return Decimal(str(value))


def _money(amount):
    """Round a Decimal dollar amount to the cent, half up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _format_money(amount):
    """Format a non-negative Decimal dollar amount as $12.50."""
    return "$" + format(_money(amount), ".2f")


def _format_percent(percent):
    """Format a Decimal percent without trailing zeros: 10, 8.25, 0."""
    text = format(Decimal(percent).normalize(), "f")
    return text


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        region = None
        discount_fraction = Decimal("0")
    else:
        customer_name = customer.name
        region = customer.region
        fraction = pricing.get_discount(customer_id)
        discount_fraction = Decimal("0") if fraction is None else _to_decimal(fraction)

    discount_percent = discount_fraction * HUNDRED

    output_lines = [f"Customer: {customer_name}"]
    subtotal = Decimal("0")
    tax_lines = []  # passed to tax.compute_tax

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output_lines.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = _money(_to_decimal(item.price))
        line_amount = _money(unit_price * quantity)
        subtotal += line_amount

        output_lines.append(
            f"{sku} x{quantity} @ {_format_money(unit_price)} = {_format_money(line_amount)}"
        )
        tax_lines.append({
            "category": item.category,
            "amount_cents": int(line_amount * 100),
        })

    subtotal = _money(subtotal)
    discount = _money(subtotal * discount_fraction)

    # tax.py returns integer cents, rounded once inside tax.py.
    tax_cents = tax.compute_tax(tax_lines, region, _format_percent_number(discount_percent))
    tax_amount = Decimal(tax_cents) / HUNDRED

    if region is None:
        tax_percent = Decimal("0")
    else:
        tax_percent = Decimal(tax.tax_pct_for_region(region))

    total = subtotal - discount + tax_amount

    output_lines.append(f"Subtotal: {_format_money(subtotal)}")
    output_lines.append(f"Discount ({_format_percent(discount_percent)}%): -{_format_money(discount)}")
    output_lines.append(f"Tax ({_format_percent(tax_percent)}%): {_format_money(tax_amount)}")
    output_lines.append(f"Total: {_format_money(total)}")

    return "\n".join(output_lines)


def _format_percent_number(percent):
    """Discount percent as a plain number for tax.compute_tax (10, 0, ...)."""
    if percent == percent.to_integral_value():
        return int(percent)
    return float(percent)
