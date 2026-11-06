"""Invoice module. Owned by agent3. Implement render_invoice(order).

Shared decisions used here (committed in the agreement log):
  units_repr:      money = int cents (1250 == $12.50); percent = number (10 == 10%);
                   a lookup miss returns None.
  pricing_api_v2:  pricing.get_item(sku) -> {sku, name, price_cents, category} or None;
                   pricing.get_customer(id) -> {id, name, discount_pct, region} or None.
  tax_api v3:      tax.compute_tax(region, discount_pct, lines) -> int tax cents
                   (region None or unknown -> 0); tax.tax_rate(region) -> float percent
                   (KeyError for unknown region).

Tax rules are NOT computed here; invoice.py only gathers the data and formats output.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format int cents as dollars, e.g. 1250 -> '$12.50', 391 -> '$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0.0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * discount_pct / 100, rounded to the cent (half up). Integer cents in and out."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _tax_percent(region):
    """Tax percent shown on the invoice; 0 when there is no region or the region is unknown."""
    if region is None:
        return 0
    try:
        return tax.tax_rate(region)
    except KeyError:
        return 0


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)
    if customer is None:
        name = customer_id
        discount_pct = 0
        region = None
    else:
        name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out_lines = []
    priced_lines = []
    subtotal = 0
    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        amount = item["price_cents"] * qty
        subtotal += amount
        priced_lines.append({"category": item["category"], "amount_cents": amount})
        out_lines.append(
            f"{sku} x{qty} @ {_money(item['price_cents'])} = {_money(amount)}"
        )

    discount = _discount_cents(subtotal, discount_pct)
    tax_cents = tax.compute_tax(region, discount_pct, priced_lines)
    total = subtotal - discount + tax_cents

    lines = [f"Customer: {name}"]
    lines.extend(out_lines)
    lines.append(f"Subtotal: {_money(subtotal)}")
    lines.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    lines.append(f"Tax ({_percent(_tax_percent(region))}%): {_money(tax_cents)}")
    lines.append(f"Total: {_money(total)}")
    return "\n".join(lines)
