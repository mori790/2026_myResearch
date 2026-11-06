"""Invoice module. Owned by agent3. Implement render_invoice(order).

All item, customer and tax information comes from pricing.py (agent1) and
tax.py (agent2). This module only formats the invoice and applies the
invoice-level discount rule.

Money is handled as decimal.Decimal in dollars (quantized to cents).
Prices from pricing.py are integer cents and are converted here.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _money(value):
    """Quantize a Decimal dollar amount to the cent (half up)."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _cents_to_dollars(cents):
    return _money(Decimal(int(cents)) / HUNDRED)


def _fmt_money(value):
    """Format a dollar amount as $12.50 (negatives as -$3.91)."""
    value = _money(value)
    if value < 0:
        return f"-${-value:.2f}"
    return f"${value:.2f}"


def _fmt_pct(pct):
    """Format a percent without trailing zeros: 10, 8.25, 0."""
    pct = Decimal(pct)
    text = format(pct.normalize(), "f")
    return text


def render_invoice(order):
    customer_id = order["customer"]
    lines_in = order["lines"]

    # Customer lookup. Unknown customer: shown by id, 0% discount, 0% tax.
    try:
        customer = pricing.get_customer(customer_id)
    except KeyError:
        customer = None

    if customer is None:
        customer_name = customer_id
        discount_pct = Decimal("0")
        region = None
    else:
        customer_name = customer.name
        discount_pct = Decimal(str(customer.discount_pct))
        region = customer.region

    out = [f"Customer: {customer_name}"]

    # Item lines. Unknown skus are reported in place and skipped.
    subtotal = Decimal("0")
    taxable_lines = []  # (category, undiscounted line amount) for tax.py
    for sku, qty in lines_in:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            out.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = _cents_to_dollars(item.price_cents)
        line_amount = _money(unit_price * qty)
        subtotal += line_amount
        taxable_lines.append((item.category, line_amount))
        out.append(
            f"{sku} x{qty} @ {_fmt_money(unit_price)} = {_fmt_money(line_amount)}"
        )

    subtotal = _money(subtotal)

    # Discount: subtotal * discount percent, rounded to the cent (half up).
    discount = _money(subtotal * discount_pct / HUNDRED)

    # Tax amount and tax percent are provided by tax.py.
    tax_amount = _money(
        tax.compute_tax(taxable_lines, region, discount_pct=discount_pct)
    )
    if region is None:
        tax_pct = Decimal("0")
    else:
        tax_pct = Decimal(str(tax.tax_rate_pct(region)))

    total = _money(subtotal - discount + tax_amount)

    out.append(f"Subtotal: {_fmt_money(subtotal)}")
    out.append(f"Discount ({_fmt_pct(discount_pct)}%): -{_fmt_money(discount)}")
    out.append(f"Tax ({_fmt_pct(tax_pct)}%): {_fmt_money(tax_amount)}")
    out.append(f"Total: {_fmt_money(total)}")

    return "\n".join(out)
