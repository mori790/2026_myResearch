"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the agreed APIs:
  pricing.get_item(sku) -> Item | None        (Item: sku, name, price[float dollars], category)
  pricing.get_customer(customer_id) -> Customer | None
                                              (Customer: id, name, discount[fraction], region)
  tax.compute_tax(lines, region, discount_pct=0) -> int cents
  tax.tax_pct_for_region(region) -> Decimal percent

Money is handled as Decimal dollars inside this module; the other modules'
float/int conventions are converted at this boundary.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _money(amount):
    """Format a Decimal dollar amount as $12.50."""
    return f"${amount.quantize(CENT, rounding=ROUND_HALF_UP):.2f}"


def _pct(value):
    """Format a Decimal percent without trailing zeros: 10 -> '10', 8.25 -> '8.25'."""
    text = format(Decimal(value).normalize(), "f")
    return text if text != "-0" else "0"


def _to_decimal(value):
    """Convert a float/int/str from another module to Decimal exactly as written."""
    return Decimal(str(value))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_name = customer.name
        discount_fraction = _to_decimal(customer.discount)
        region = customer.region

    lines_out = [f"Customer: {customer_name}"]
    subtotal = Decimal("0")
    taxable_lines = []  # (category, amount_cents) for known SKUs, in order

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            lines_out.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = _to_decimal(item.price).quantize(CENT, rounding=ROUND_HALF_UP)
        line_amount = unit_price * quantity
        subtotal += line_amount
        taxable_lines.append((item.category, int(line_amount * HUNDRED)))
        lines_out.append(
            f"{sku} x{quantity} @ {_money(unit_price)} = {_money(line_amount)}"
        )

    discount_percent = discount_fraction * HUNDRED
    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_cents = tax.compute_tax(taxable_lines, region, _percent_arg(discount_percent))
    tax_amount = Decimal(tax_cents) / HUNDRED
    if region is None:
        tax_percent = Decimal("0")
    else:
        tax_percent = Decimal(str(tax.tax_pct_for_region(region)))

    total = subtotal - discount + tax_amount

    lines_out.append(f"Subtotal: {_money(subtotal)}")
    lines_out.append(f"Discount ({_pct(discount_percent)}%): -{_money(discount)}")
    lines_out.append(f"Tax ({_pct(tax_percent)}%): {_money(tax_amount)}")
    lines_out.append(f"Total: {_money(total)}")
    return "\n".join(lines_out)


def _percent_arg(percent):
    """Pass the discount percent as int when whole (e.g. 10), otherwise as float."""
    if percent == percent.to_integral_value():
        return int(percent)
    return float(percent)
