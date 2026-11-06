"""Invoice module. Owned by agent3. Implement render_invoice(order).

Cross-module calls follow the agreed APIs:
  pricing.get_item(sku)            -> Item(sku, name, unit_price, category) or None
                                      (unit_price: float dollars)
  pricing.get_customer(cid)        -> Customer(customer_id, name, discount_rate, region) or None
                                      (discount_rate: float fraction, 0.10 = 10%)
  tax.compute_tax(lines, region, discount_pct) -> int cents
                                      lines = [(category, amount_cents), ...]
                                      region None -> 0 tax; discount_pct is a percent number
  tax.tax_pct_for_region(region)   -> Decimal percent (e.g. Decimal("8.25")); None -> 0

Money is converted to decimal.Decimal dollars at this boundary (team standard).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(value):
    """Convert a float/int/str dollar amount to a Decimal rounded to the cent."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _percent_text(value):
    """Format a Decimal percent without trailing zeros (10, 8.25, 0)."""
    text = format(Decimal(value).normalize(), "f")
    return text


def _fmt_dollars(amount):
    """Format a Decimal dollar amount with two decimals, e.g. 37.05."""
    return "{:.2f}".format(amount)


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_label = customer_id
        discount_rate = Decimal("0")
        region = None
    else:
        customer_label = customer.name
        discount_rate = Decimal(str(customer.discount_rate))
        region = customer.region

    out_lines = [f"Customer: {customer_label}"]

    subtotal = Decimal("0.00")
    tax_lines = []  # (category, amount_cents) for tax.py

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = _money(item.unit_price)
        line_amount = (unit_price * quantity).quantize(CENT, rounding=ROUND_HALF_UP)
        subtotal += line_amount
        out_lines.append(
            f"{sku} x{quantity} @ ${_fmt_dollars(unit_price)} "
            f"= ${_fmt_dollars(line_amount)}"
        )
        tax_lines.append((item.category, int((line_amount * 100).to_integral_value(rounding=ROUND_HALF_UP))))

    discount_percent = discount_rate * 100  # Decimal percent, e.g. 10
    discount = (subtotal * discount_rate).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_cents = tax.compute_tax(tax_lines, region, float(discount_percent))
    tax_amount = (Decimal(tax_cents) / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_percent = Decimal(str(tax.tax_pct_for_region(region)))

    total = subtotal - discount + tax_amount

    out_lines.append(f"Subtotal: ${_fmt_dollars(subtotal)}")
    out_lines.append(f"Discount ({_percent_text(discount_percent)}%): -${_fmt_dollars(discount)}")
    out_lines.append(f"Tax ({_percent_text(tax_percent)}%): ${_fmt_dollars(tax_amount)}")
    out_lines.append(f"Total: ${_fmt_dollars(total)}")

    return "\n".join(out_lines)
