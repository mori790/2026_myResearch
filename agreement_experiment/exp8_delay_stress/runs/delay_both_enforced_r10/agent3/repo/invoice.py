"""Invoice module. Owned by agent3. Implement render_invoice(order).

Committed team decisions this module follows:
  MONEY_UNIT (v4): all arithmetic and cross-module money is integer cents.
      Items carry price_cents (int). The float 'price' is display-only and is never used here.
  PERCENT_REPR (v2): percentages are fractions (0.10 = 10%) in every cross-module field.
  MISSING_LOOKUP_VALUE (v2): pricing.get_item / get_customer return None when not found.
  TAX_API (v3): tax.tax_breakdown(region, lines, discount_rate) -> (rate, amount_cents)
      lines = list of (category, amount_cents) for known SKUs, in order.
      rate = fraction (0.0825), amount_cents = int, rounded half-up.
  TAX_UNKNOWN_REGION (v1): region None -> 0% tax, no error.

Pricing record shapes (agent1):
  get_item(sku)      -> {'sku', 'name', 'category', 'price', 'price_cents'} or None
  get_customer(cid)  -> {'id', 'name', 'region', 'discount'} or None   (discount is a fraction)
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _round_half_up(value):
    """Round a Decimal to an integer number of cents, half up."""
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format integer cents as dollars, e.g. 1250 -> '$12.50', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros, e.g. 0.0825 -> '8.25', 0.10 -> '10', 0 -> '0'."""
    percent = (Decimal(str(fraction)) * 100).normalize()
    return format(percent, "f")


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_label = customer_id
        region = None
        discount_rate = Decimal("0")
    else:
        customer_label = customer.get("name") or customer_id
        region = customer.get("region")
        discount_rate = Decimal(str(customer.get("discount") or 0))

    out_lines = [f"Customer: {customer_label}"]
    tax_lines = []  # (category, amount_cents) for known SKUs only
    subtotal_cents = 0

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = int(item["price_cents"])
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        tax_lines.append((item.get("category"), amount_cents))
        out_lines.append(
            f"{sku} x{quantity} @ {_money(unit_cents)} = {_money(amount_cents)}"
        )

    discount_cents = _round_half_up(Decimal(subtotal_cents) * discount_rate)

    tax_rate, tax_cents = tax.tax_breakdown(region, tax_lines, discount_rate)
    tax_cents = int(tax_cents)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append(f"Subtotal: {_money(subtotal_cents)}")
    out_lines.append(f"Discount ({_percent(discount_rate)}%): -{_money(discount_cents)}")
    out_lines.append(f"Tax ({_percent(tax_rate)}%): {_money(tax_cents)}")
    out_lines.append(f"Total: {_money(total_cents)}")

    return "\n".join(out_lines)
