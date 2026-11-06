"""Invoice module. Owned by agent3. Implements render_invoice(order).

Uses the committed interfaces:
  pricing_api v2: get_item(sku), get_customer(customer_id)  (None when unknown)
  tax_api v2:     sales_tax(region, lines, discount_percent)
                  -> {"tax_cents": int, "rate_percent": str}
All money is int cents. Percents are decimal strings. This module computes
only the subtotal and the discount; every tax rule lives in tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format int cents as $X.YY, with a leading '-' for negative amounts."""
    sign = "-" if cents < 0 else ""
    a = abs(cents)
    return f"{sign}${a // 100}.{a % 100:02d}"


def _percent(value):
    """Format a percent with no trailing zeros: '10', '8.25', '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount. Tax is 0% via tax.py
        # (region None is the agreed signal for unknown customers).
        name = customer_id
        discount_percent = "0"
        region = None
    else:
        name = customer["name"]
        discount_percent = _percent(customer["discount_percent"])
        region = customer["region"]

    out = [f"Customer: {name}"]

    priced_lines = []  # [sku, category, gross_line_cents] for known items
    subtotal_cents = 0
    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = item["unit_price_cents"]
        amount = unit * quantity
        subtotal_cents += amount
        priced_lines.append([sku, item["category"], amount])
        out.append(f"{sku} x{quantity} @ {_money(unit)} = {_money(amount)}")

    discount_cents = int(
        (Decimal(subtotal_cents) * Decimal(discount_percent) / Decimal(100))
        .quantize(Decimal(1), rounding=ROUND_HALF_UP)
    )

    tax_result = tax.sales_tax(region, priced_lines, discount_percent)
    tax_cents = tax_result["tax_cents"]
    tax_rate = _percent(tax_result["rate_percent"])

    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append(f"Subtotal: {_money(subtotal_cents)}")
    out.append(f"Discount ({discount_percent}%): -{_money(discount_cents)}")
    out.append(f"Tax ({tax_rate}%): {_money(tax_cents)}")
    out.append(f"Total: {_money(total_cents)}")
    return "\n".join(out)
