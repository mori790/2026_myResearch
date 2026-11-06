"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the APIs agreed in the team log:
  pricing (agent1): get_item(sku) -> {sku, name, price, category} or None
                    get_customer(cid) -> {id, name, discount (fraction), region} or None
  tax (agent2):     sales_tax_cents(region, lines, discount_pct) -> int cents
                    tax_rate_pct(region) -> float (KeyError if unknown region)

Money is handled as integer cents at the boundary with tax.py; percents are
shown as percent numbers. This module computes no tax rules itself.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(amount):
    """Decimal dollars -> int cents, rounded half up to the cent."""
    return int(Decimal(amount).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _fmt_money(cents):
    """int cents -> '$12.50' or '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _fmt_percent(value):
    """Percent without trailing zeros: 10.0 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = format(Decimal(str(value)).normalize(), "f")
    return "0" if text in ("-0", "") else text


def render_invoice(order):
    customer_id = order.get("customer", "")
    cust = pricing.get_customer(customer_id)  # None for unknown customer
    if cust:
        name = cust.get("name") or str(customer_id)
        discount_frac = Decimal(str(cust.get("discount") or 0))
        region = cust.get("region")
    else:
        name = str(customer_id)
        discount_frac = Decimal("0")
        region = None
    discount_pct = discount_frac * 100

    out_lines = [f"Customer: {name}"]
    tax_lines = []  # (category, line_amount_cents) for known skus only
    subtotal_cents = 0

    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = Decimal(str(item["price"]))
        line_cents = _to_cents(unit * Decimal(qty) * 100)
        subtotal_cents += line_cents
        tax_lines.append((item.get("category", ""), line_cents))
        out_lines.append(
            f"{sku} x{qty} @ {_fmt_money(_to_cents(unit * 100))} = {_fmt_money(line_cents)}"
        )

    discount_cents = _to_cents(Decimal(subtotal_cents) * discount_frac)

    if region is None:
        tax_cents = 0
        tax_pct = 0
    else:
        tax_cents = tax.sales_tax_cents(region, tax_lines, float(discount_pct))
        tax_pct = tax.tax_rate_pct(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append(f"Subtotal: {_fmt_money(subtotal_cents)}")
    out_lines.append(f"Discount ({_fmt_percent(discount_pct)}%): -{_fmt_money(discount_cents)}")
    out_lines.append(f"Tax ({_fmt_percent(tax_pct)}%): {_fmt_money(tax_cents)}")
    out_lines.append(f"Total: {_fmt_money(total_cents)}")

    return "\n".join(out_lines)
