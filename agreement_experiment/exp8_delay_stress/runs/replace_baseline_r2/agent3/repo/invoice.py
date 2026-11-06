"""Invoice module. Owned by agent3. Implement render_invoice(order).

Team convention (this module): money is decimal.Decimal in dollars, percents
are multipliers, and a missing lookup gives a default.

Other modules use different units (agreed on the decision log):
  - pricing.get_item / get_customer: float dollars, discount as a fraction (0.10)
  - tax.compute_tax: integer cents, percent numbers (10 = 10% off)
Conversion to and from those units happens only in this file.

Rules implemented here (invoice rules, not tax rules):
  - line amount = unit price * quantity
  - unknown SKUs are shown as "UNKNOWN SKU: <sku>" and left out of the sums
  - discount = subtotal * discount percent, rounded to the cent (half up)
  - tax amount and tax percent come from tax.compute_tax
  - total = subtotal - discount + tax
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _dec(value):
    """Convert a number from another module to Decimal without float noise."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _to_cents(amount):
    """Round a Decimal dollar amount to the cent (half up) and return it."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _usd(amount):
    """Format a Decimal dollar amount as $12.50 (negative values get a leading minus)."""
    amount = _to_cents(amount)
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):.2f}"


def _percent(value):
    """Format a percent number without trailing zeros: 10, 8.25, 0."""
    text = format(_dec(value).normalize(), "f")
    return text


def render_invoice(order):
    customer_id = order["customer"]
    lines_in = order.get("lines", [])

    # Customer lookup. Unknown customer: shown by id, 0% discount, no tax region.
    customer = pricing.get_customer(customer_id)
    if customer is None:
        customer_label = str(customer_id)
        discount_pct = Decimal("0")
        region = None
    else:
        customer_label = customer["name"]
        # pricing gives a fraction (0.10 = 10% off); convert to a percent number.
        discount_pct = _dec(customer["discount"]) * HUNDRED
        region = customer["region"]

    out = [f"Customer: {customer_label}"]
    subtotal = Decimal("0")
    tax_lines = []  # (category, amount_cents) for tax.compute_tax

    for sku, quantity in lines_in:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = _to_cents(_dec(item["price"]))
        qty = _dec(quantity)
        amount = _to_cents(unit_price * qty)

        subtotal += amount
        out.append(f"{sku} x{_percent(qty)} @ {_usd(unit_price)} = {_usd(amount)}")
        tax_lines.append((item["category"], int(amount * 100)))

    # Discount is an invoice rule, computed here and rounded half up to the cent.
    discount = _to_cents(subtotal * discount_pct / HUNDRED)

    # Tax comes from tax.py. It applies the discount itself to the taxable base,
    # so pass the discount percent and do not pre-discount the lines.
    result = tax.compute_tax(tax_lines, region, discount_pct)
    tax_amount = _to_cents(Decimal(result.tax_cents) / 100)
    tax_pct = _percent(result.tax_pct)

    total = _to_cents(subtotal - discount + tax_amount)

    out.append(f"Subtotal: {_usd(subtotal)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_usd(discount)}")
    out.append(f"Tax ({tax_pct}%): {_usd(tax_amount)}")
    out.append(f"Total: {_usd(total)}")

    return "\n".join(out)
