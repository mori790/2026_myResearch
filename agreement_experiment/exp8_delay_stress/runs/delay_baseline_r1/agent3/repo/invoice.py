"""Invoice module. Owned by agent3. Implement render_invoice(order).

Data sources (no tax rules or catalog data live here):
  pricing.get_item(sku)          -> {'sku','name','price','category'} or None   (price: float dollars)
  pricing.get_customer(cid)      -> {'id','name','discount','region'} or None   (discount: fraction, 0.10 = 10%)
  tax.calculate_tax(region, lines, discount_pct) -> int cents
      lines: [(category, line_amount_cents), ...], discount_pct: percent (e.g. 10), region None -> 0 tax
  tax.tax_pct_for_region(region) -> Decimal percent (e.g. Decimal('8.25'))

Money inside this module is decimal.Decimal in dollars.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")
ZERO = Decimal("0")


def _money(amount):
    """Format a Decimal dollar amount as '$12.50' (negative: '-$3.91')."""
    q = amount.quantize(CENT, rounding=ROUND_HALF_UP)
    if q < 0:
        return "-$" + format(-q, ".2f")
    return "$" + format(q, ".2f")


def _percent(value):
    """Format a Decimal percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = format(Decimal(value).normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("", "-0"):
        text = "0"
    return text


def _to_decimal(value):
    """Convert a float/int/str value from pricing into Decimal without float artifacts."""
    return Decimal(str(value))


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_label = customer_id
        region = None
        discount_fraction = ZERO
    else:
        customer_label = customer.get("name") or customer_id
        region = customer.get("region")
        discount_fraction = _to_decimal(customer.get("discount") or 0)

    discount_pct = discount_fraction * HUNDRED  # e.g. Decimal('10')

    output = ["Customer: " + str(customer_label)]

    subtotal = ZERO
    taxable_lines = []  # (category, line_amount_cents), before discount, for tax.py
    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            output.append("UNKNOWN SKU: " + str(sku))
            continue

        unit_price = _to_decimal(item.get("price") or 0)
        quantity = int(quantity)
        line_amount = (unit_price * quantity).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += line_amount
        taxable_lines.append((item.get("category") or "", int(line_amount * HUNDRED)))

        output.append(
            "{} x{} @ {} = {}".format(
                sku, quantity, _money(unit_price), _money(line_amount)
            )
        )

    subtotal = subtotal.quantize(CENT, rounding=ROUND_HALF_UP)

    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_cents = tax.calculate_tax(region, taxable_lines, discount_pct)
    tax_amount = Decimal(tax_cents) / HUNDRED
    tax_pct = tax.tax_pct_for_region(region) if region is not None else ZERO

    total = subtotal - discount + tax_amount

    output.append("Subtotal: " + _money(subtotal))
    output.append("Discount ({}%): -{}".format(_percent(discount_pct), _money(discount)))
    output.append("Tax ({}%): {}".format(_percent(tax_pct), _money(tax_amount)))
    output.append("Total: " + _money(total))

    return "\n".join(output)
