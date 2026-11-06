"""Invoice module. Owned by agent3.

render_invoice(order) gets item, customer and tax information from
pricing.py and tax.py. It does not implement any tax rules itself.

Committed interfaces (agreement log: pricing_api v2, tax_api v1):
  pricing.get_item(sku)          -> dict(sku, name, unit_price_cents: int, category) or None
  pricing.get_customer(cust_id)  -> dict(id, name, discount_pct: number, region: str) or None
  tax.compute_tax(lines, region, discount_pct) -> int cents
      lines = [{"amount_cents": int, "category": str}, ...]
  tax.tax_rate(region)           -> Decimal percent (KeyError if region unknown)

Money is handled in integer cents and percentages are percent numbers, as
committed. Discount is rounded half up to the cent. Output is formatted here.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _cents_text(cents):
    """Format an integer cent amount as dollars: 1250 -> '12.50', -391 -> '-3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def _percent_text(percent):
    """Format a percent without trailing zeros: 10, 8.25, 0."""
    value = Decimal(str(percent))
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_label = customer_id
        discount_pct = 0
        region = None
    else:
        customer_label = customer["name"] or customer_id
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out_lines = [f"Customer: {customer_label}"]

    subtotal_cents = 0
    tax_lines = []

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_cents = item["unit_price_cents"]
        line_cents = unit_cents * quantity
        subtotal_cents += line_cents
        tax_lines.append({"amount_cents": line_cents, "category": item["category"]})

        out_lines.append(
            f"{sku} x{quantity} @ ${_cents_text(unit_cents)} = ${_cents_text(line_cents)}"
        )

    # Discount: subtotal * percent / 100, rounded half up to the cent.
    discount_cents = int(
        (Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100))
        .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    # Tax is computed by tax.py, which applies the discount to the taxable base.
    tax_cents = tax.compute_tax(tax_lines, region, discount_pct)

    if region is None:
        tax_pct = 0
    else:
        try:
            tax_pct = tax.tax_rate(region)
        except KeyError:
            tax_pct = 0

    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append(f"Subtotal: ${_cents_text(subtotal_cents)}")
    out_lines.append(f"Discount ({_percent_text(discount_pct)}%): -${_cents_text(discount_cents)}")
    out_lines.append(f"Tax ({_percent_text(tax_pct)}%): ${_cents_text(tax_cents)}")
    out_lines.append(f"Total: ${_cents_text(total_cents)}")

    return "\n".join(out_lines)
