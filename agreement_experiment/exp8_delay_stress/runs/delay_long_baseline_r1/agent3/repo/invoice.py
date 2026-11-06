"""Invoice module. Owned by agent3. Implement render_invoice(order).

Depends on:
  pricing.get_item(sku)       -> Item(sku, name, price, category) or None   (price: float dollars)
  pricing.get_customer(cid)   -> Customer(id, name, discount, region) or None (discount: fraction, e.g. 0.10)
  tax.compute_tax_cents(lines, region, discount_pct=0) -> int cents
      lines = [(category, amount_cents)] pre-discount; region None = unknown customer (0 tax)
  tax.get_rate_percent(region) -> Decimal percent (e.g. Decimal('8.25')) for display

Money is handled internally as integer cents; percents as Decimal.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(dollars):
    """Convert a float/Decimal dollar amount to integer cents (half up)."""
    value = Decimal(str(dollars)) * 100
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _fmt_money(cents):
    """Format non-negative integer cents as '$12.50'."""
    return f"${cents // 100}.{cents % 100:02d}"


def _fmt_percent(value):
    """Format a percent without trailing zeros: 10, 8.25, 0."""
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_name = customer_id
        discount_pct = Decimal("0")
        region = None
    else:
        customer_name = customer.name
        discount_pct = Decimal(str(customer.discount)) * 100  # 0.10 -> 10
        region = customer.region

    out_lines = [f"Customer: {customer_name}"]
    priced_lines = []  # (category, amount_cents) for tax.py
    subtotal_cents = 0

    for entry in order["lines"]:
        sku, qty = entry[0], int(entry[1])
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = _to_cents(item.price)
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        priced_lines.append((item.category, amount_cents))
        out_lines.append(
            f"{sku} x{qty} @ {_fmt_money(unit_cents)} = {_fmt_money(amount_cents)}"
        )

    # Discount = subtotal * discount percent, rounded to the cent (half up).
    discount_cents = int(
        (Decimal(subtotal_cents) * discount_pct / 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )

    # Tax amount and displayed rate come from tax.py only.
    tax_cents = tax.compute_tax_cents(priced_lines, region, discount_pct=float(discount_pct))
    tax_percent = Decimal("0") if region is None else Decimal(str(tax.get_rate_percent(region)))

    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append(f"Subtotal: {_fmt_money(subtotal_cents)}")
    out_lines.append(f"Discount ({_fmt_percent(discount_pct)}%): -{_fmt_money(discount_cents)}")
    out_lines.append(f"Tax ({_fmt_percent(tax_percent)}%): {_fmt_money(tax_cents)}")
    out_lines.append(f"Total: {_fmt_money(total_cents)}")

    return "\n".join(out_lines)
