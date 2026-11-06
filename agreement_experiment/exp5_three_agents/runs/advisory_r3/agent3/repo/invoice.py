"""Invoice module. Owned by agent3. Implements render_invoice(order).

Agreed interfaces (see agree.py log):
  money_representation : all money is integer cents.
  percent_representation: percents are decimal.Decimal.
  pricing_api_v2       : pricing.get_unit_price_cents(sku) -> int | None
                         pricing.get_customer_discount_percent(cid) -> Decimal | None
                         pricing.get_customer_region(cid) -> str | None
                         pricing.get_item_category(sku) -> str | None
  tax_interface        : tax.calculate_tax(region, lines, discount_pct)
                         -> (tax_cents: int, tax_percent: Decimal)
                         lines = [(category, amount_cents), ...] undiscounted.
  discount_display     : discount_cents = round_half_up(subtotal * pct / 100);
                         total = subtotal - discount + tax.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _fmt_money(cents):
    """Format integer cents as '$12.50' (negative as '-$3.91')."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _fmt_percent(value):
    """Format a Decimal percent without trailing zeros: 10, 8.25, 0."""
    text = format(Decimal(value).normalize(), "f")
    return text


def _round_half_up(value):
    """Round a Decimal to an integer (cents) with half-up rounding."""
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]

    # Customer data. Unknown customer: 0% discount, tax handled as region None.
    discount_pct = pricing.get_customer_discount_percent(customer_id)
    if discount_pct is None:
        discount_pct = Decimal("0")
    else:
        discount_pct = Decimal(str(discount_pct))
    region = pricing.get_customer_region(customer_id)

    lines_out = []   # text lines in order
    taxable_lines = []  # (category, amount_cents) for tax.py
    subtotal_cents = 0

    for sku, qty in order["lines"]:
        unit_price = pricing.get_unit_price_cents(sku)
        if unit_price is None:
            lines_out.append(f"UNKNOWN SKU: {sku}")
            continue
        amount = unit_price * qty
        subtotal_cents += amount
        lines_out.append(f"{sku} x{qty} @ {_fmt_money(unit_price)} = {_fmt_money(amount)}")
        taxable_lines.append((pricing.get_item_category(sku), amount))

    discount_cents = _round_half_up(Decimal(subtotal_cents) * discount_pct / 100)

    tax_cents, tax_percent = tax.calculate_tax(region, taxable_lines, discount_pct)
    tax_cents = int(tax_cents)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out = [f"Customer: {customer_id}"]
    out.extend(lines_out)
    out.append(f"Subtotal: {_fmt_money(subtotal_cents)}")
    out.append(f"Discount ({_fmt_percent(discount_pct)}%): -{_fmt_money(discount_cents)}")
    out.append(f"Tax ({_fmt_percent(tax_percent)}%): {_fmt_money(tax_cents)}")
    out.append(f"Total: {_fmt_money(total_cents)}")
    return "\n".join(out)
