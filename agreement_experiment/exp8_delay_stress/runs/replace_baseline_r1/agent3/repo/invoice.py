"""Invoice module. Owned by agent3.

render_invoice(order) gets item, customer and tax information from
pricing.py and tax.py. It does not compute tax rules itself.

Money inside this module is decimal.Decimal in dollars. pricing.py returns
floats in dollars and tax.py takes int cents, so conversions happen only at
those two boundaries.

Interfaces used (agreed with the other modules):
  pricing.get_item(sku)          -> {'sku','name','price','category'} or None
  pricing.get_customer(cid)      -> {'id','name','discount','region'} or None
                                    discount is a fraction (0.10 = 10%)
  tax.compute_tax(lines, discount_pct, region) -> int cents
                                    lines = [(category, amount_cents), ...]
                                    discount_pct = percent (10 = 10%)
                                    region None = unknown customer, 0 tax
  tax.tax_pct_for_region(region) -> Decimal percent (None -> 0)
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(value):
    """Decimal dollars -> Decimal rounded to the cent (half up)."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _to_decimal(value):
    """float/int/str from pricing.py -> Decimal, via str() to avoid float noise."""
    return Decimal(str(value))


def _fmt_money(value):
    """Decimal dollars -> '12.50'. Negative sign is added by the caller."""
    return f"{_money(value):.2f}"


def _fmt_percent(value):
    """Percent without trailing zeros: 10, 8.25, 0."""
    text = format(Decimal(value).normalize(), "f")
    # Decimal('0.00').normalize() gives '0' already; guard against '-0'.
    return "0" if text in ("-0", "") else text


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_name = customer.get("name") or customer_id
        discount_fraction = _to_decimal(customer.get("discount") or 0)
        region = customer.get("region") or None

    lines_out = []
    priced_lines = []  # (category, amount_cents) for tax.py
    subtotal = Decimal("0")

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            lines_out.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = _to_decimal(item["price"])
        amount = unit_price * quantity
        subtotal += amount
        lines_out.append(
            f"{sku} x{quantity} @ ${_fmt_money(unit_price)} = ${_fmt_money(amount)}"
        )
        priced_lines.append((item.get("category") or "", int(_money(amount) * 100)))

    subtotal = _money(subtotal)

    discount_pct = discount_fraction * 100
    discount = _money(subtotal * discount_fraction)

    tax_cents = tax.compute_tax(priced_lines, discount_pct, region)
    tax_amount = Decimal(tax_cents) / 100
    tax_pct = Decimal(tax.tax_pct_for_region(region))

    total = _money(subtotal - discount + tax_amount)

    lines_out.extend(
        [
            f"Subtotal: ${_fmt_money(subtotal)}",
            f"Discount ({_fmt_percent(discount_pct)}%): -${_fmt_money(discount)}",
            f"Tax ({_fmt_percent(tax_pct)}%): ${_fmt_money(tax_amount)}",
            f"Total: ${_fmt_money(total)}",
        ]
    )
    return "\n".join([f"Customer: {customer_name}"] + lines_out)
