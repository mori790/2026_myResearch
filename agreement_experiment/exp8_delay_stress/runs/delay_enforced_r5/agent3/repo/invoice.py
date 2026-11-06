"""Invoice module. Owned by agent3. Implement render_invoice(order).

Committed APIs (agree.py topics 'pricing_api' v3 and 'tax_api' v2):
  pricing.get_item(sku) -> dict
      {"sku", "name", "unit_price_cents": int, "category"}; raises KeyError if sku unknown
  pricing.get_customer(customer_id) -> dict
      {"id", "name", "discount_pct": int (10 = 10%), "region"}; raises KeyError if id unknown
  tax.compute_tax(region, lines, discount_pct) -> int tax in cents
      lines = [{"category": str, "amount_cents": int}]; region None -> 0
  tax.rate_percent(region) -> float (8.25 = 8.25%); display only, region None -> 0

All money math here is in integer cents (the committed unit), with exact
integer arithmetic for the discount. Tax is never computed in this module.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _cents_text(cents):
    """Format integer cents as dollars, e.g. 1250 -> '$12.50', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent_text(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0.0 -> '0'."""
    d = Decimal(str(value)).normalize()
    return format(d, "f")


def render_invoice(order):
    customer_id = order.get("customer", "")

    try:
        customer = pricing.get_customer(customer_id)
    except KeyError:
        # Unknown customer: shown by its id, 0% discount, and 0% tax (region None).
        customer = None

    if customer is None:
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out_lines = [f"Customer: {customer_name}"]
    tax_lines = []
    subtotal_cents = 0

    for sku, qty in order.get("lines", []):
        qty = int(qty)
        try:
            item = pricing.get_item(sku)
        except KeyError:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_cents = item["unit_price_cents"]
        amount_cents = unit_cents * qty
        subtotal_cents += amount_cents
        out_lines.append(
            f"{sku} x{qty} @ {_cents_text(unit_cents)} = {_cents_text(amount_cents)}"
        )
        tax_lines.append({
            "category": item["category"],
            "amount_cents": amount_cents,
        })

    # Discount = subtotal * discount_pct / 100, rounded to the cent, half up.
    discount_cents = int(
        (Decimal(subtotal_cents) * Decimal(discount_pct) / Decimal(100))
        .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    tax_cents = tax.compute_tax(region, tax_lines, discount_pct)
    tax_percent = tax.rate_percent(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append(f"Subtotal: {_cents_text(subtotal_cents)}")
    out_lines.append(
        f"Discount ({_percent_text(discount_pct)}%): -{_cents_text(discount_cents)}"
    )
    out_lines.append(f"Tax ({_percent_text(tax_percent)}%): {_cents_text(tax_cents)}")
    out_lines.append(f"Total: {_cents_text(total_cents)}")

    return "\n".join(out_lines)
