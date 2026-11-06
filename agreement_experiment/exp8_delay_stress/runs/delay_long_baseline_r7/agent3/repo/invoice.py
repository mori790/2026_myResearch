"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the agreed APIs:
  pricing.py (agent1, as implemented):
    get_item(sku) -> {'sku', 'name', 'price' (float dollars), 'category'} or None
    get_customer(cust_id) -> {'id', 'name', 'discount' (fraction, e.g. 0.15), 'region'} or None
  tax.py (agent2, tax_api):
    tax_pct(region) -> percent number (region None -> 0)
    compute_tax(lines, region, discount_pct) -> tax in integer cents
      lines = [(category, amount_cents)], discount_pct = percent number

Money is handled as integer cents internally; floats from pricing are converted
via Decimal(str(...)) to avoid binary float error. Only display strings are
produced here; no tax rules live in this module.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(dollars):
    """Convert a float/Decimal dollar amount to integer cents (half up)."""
    exact = Decimal(str(dollars)) * 100
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format integer cents as a dollar string, e.g. 1250 -> '$12.50', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "{}${}.{:02d}".format(sign, cents // 100, cents % 100)


def _percent(value):
    """Format a percent number without trailing zeros, e.g. 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    d = Decimal(str(value))
    text = format(d.normalize(), "f")
    if text in ("-0", ""):
        text = "0"
    return text


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * discount percent, rounded to the cent (half up)."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        region = None
        discount_pct = 0
    else:
        customer_name = customer["name"]
        region = customer["region"]
        # pricing gives a fraction (0.15); tax_api and display use percent (15).
        discount_pct = float(Decimal(str(customer["discount"])) * 100)

    out_lines = ["Customer: {}".format(customer_name)]
    tax_lines = []  # (category, amount_cents) for known items only
    subtotal_cents = 0

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: {}".format(sku))
            continue
        unit_price_cents = _to_cents(item["price"])
        category = item["category"]
        amount_cents = unit_price_cents * quantity
        subtotal_cents += amount_cents
        tax_lines.append((category, amount_cents))
        out_lines.append("{} x{} @ {} = {}".format(
            sku, quantity, _money(unit_price_cents), _money(amount_cents)))

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    tax_cents = tax.compute_tax(tax_lines, region, discount_pct)
    tax_pct = tax.tax_pct(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append("Subtotal: {}".format(_money(subtotal_cents)))
    # Discount is always shown with a minus sign, even when it is $0.00 ("-$0.00").
    out_lines.append("Discount ({}%): -{}".format(
        _percent(discount_pct), _money(discount_cents)))
    out_lines.append("Tax ({}%): {}".format(_percent(tax_pct), _money(tax_cents)))
    out_lines.append("Total: {}".format(_money(total_cents)))

    return "\n".join(out_lines)
