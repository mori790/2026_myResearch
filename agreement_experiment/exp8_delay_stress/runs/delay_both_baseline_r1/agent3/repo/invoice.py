"""Invoice module. Owned by agent3. Implement render_invoice(order).

Facts come from other modules and are never recomputed here:
  pricing.get_item(sku)          -> Item(sku, name, price: float dollars, category) | None
  pricing.get_customer(cid)      -> Customer(id, name, discount: float fraction, region) | None
  tax.tax_pct_for_region(region) -> Decimal percent (e.g. 8.25); None region -> 0
  tax.compute_tax(region, discount_pct, lines) -> int cents
      lines = [(category, line_amount_cents)] before discount, quantity already applied

Internally money is kept in integer cents with Decimal rounding (half up).
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(dollars):
    """Convert a float or Decimal dollar amount to integer cents (half up)."""
    return int((Decimal(str(dollars)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format non-negative integer cents as $12.50."""
    return f"${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = format(Decimal(str(value)).normalize(), "f")
    return "0" if text in ("-0", "-0.0") else text


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_name = customer.name
        discount_fraction = Decimal(str(customer.discount))
        region = customer.region

    discount_percent = discount_fraction * 100
    tax_percent = Decimal(str(tax.tax_pct_for_region(region)))

    out = [f"Customer: {customer_name}"]
    tax_lines = []  # (category, line amount in cents before discount)
    subtotal_cents = 0

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = _to_cents(item.price)
        line_cents = unit_cents * qty
        subtotal_cents += line_cents
        tax_lines.append((item.category, line_cents))
        out.append(f"{sku} x{qty} @ {_money(unit_cents)} = {_money(line_cents)}")

    # discount = subtotal * discount fraction, rounded to the cent (half up)
    discount_cents = int(
        (Decimal(subtotal_cents) * discount_fraction).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    # tax.py applies the discount itself and returns tax in integer cents.
    tax_cents = tax.compute_tax(region, float(discount_percent), tax_lines)

    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append(f"Subtotal: {_money(subtotal_cents)}")
    out.append(f"Discount ({_percent(discount_percent)}%): -{_money(discount_cents)}")
    out.append(f"Tax ({_percent(tax_percent)}%): {_money(tax_cents)}")
    out.append(f"Total: {_money(total_cents)}")
    return "\n".join(out)
