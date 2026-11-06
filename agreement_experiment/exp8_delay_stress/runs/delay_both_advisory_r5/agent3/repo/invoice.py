"""Invoice module. Owned by agent3. Implement render_invoice(order).

Interfaces used (committed in the shared decision log):
- pricing_api v3: get_item(sku) -> {sku, name, unit_price_cents, category}, KeyError if unknown;
                  get_customer(customer_id) -> {id, name, discount_pct, region}, KeyError if unknown.
- tax_interface v1: tax.compute_tax(region, lines, discount_pct) -> int cents (half up).
                    region None means unknown customer (tax 0).
- tax_rate v1: tax.rate_percent(region) -> percent number (8.25 means 8.25%), 0 for None.

Money is computed in integer cents here; percents are percent numbers (10 means 10%).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as a dollar string: 1250 -> '$12.50', 0 -> '$0.00'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    try:
        customer = pricing.get_customer(customer_id)
    except KeyError:
        customer = None

    if customer is None:
        name = customer_id
        discount_pct = 0
        region = None  # tax.py treats None as an unknown customer: 0% tax
    else:
        name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out = [f"Customer: {name}"]
    taxable_lines = []
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = item["unit_price_cents"]
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        out.append(f"{sku} x{quantity} @ {_money(unit_cents)} = {_money(amount_cents)}")
        taxable_lines.append({"category": item["category"], "amount_cents": amount_cents})

    # Discount = subtotal * percent / 100, rounded to the cent, half up.
    discount_cents = int(
        (Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100))
        .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    # Tax amount and tax percent come from tax.py; invoice.py does not apply tax rules.
    tax_cents = tax.compute_tax(region, taxable_lines, discount_pct)
    tax_pct = tax.rate_percent(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append(f"Subtotal: {_money(subtotal_cents)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount_cents)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_cents)}")
    out.append(f"Total: {_money(total_cents)}")
    return "\n".join(out)
