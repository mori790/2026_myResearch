"""Invoice module. Owned by agent3. Implement render_invoice(order).

Interfaces used (committed in the shared decision log):
  pricing.get_item(sku)          -> dict {sku, name, price_cents:int, category} or None
  pricing.get_customer(cid)      -> dict {id, name, discount_pct:number, region:str} or None
  tax.compute_tax(region, lines, discount_pct) -> int cents
      lines = [{"category": str, "amount_cents": int}, ...]
  tax.tax_rate_pct(region)       -> number (percent, e.g. 8.25)

This module does no tax computation itself. Discount is applied here
(committed: "Discount is applied by invoice, not pricing").
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as dollars, e.g. 2500 -> '$25.00'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s$%d.%02d" % (sign, cents // 100, cents % 100)


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    d = Decimal(str(value)).normalize()
    return format(d, "f")


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * discount_pct / 100, rounded to the cent, half up."""
    exact = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None -> tax 0).
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out_lines = ["Customer: %s" % customer_name]
    tax_lines = []
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: %s" % sku)
            continue
        unit_cents = item["price_cents"]
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        tax_lines.append({"category": item["category"], "amount_cents": amount_cents})
        out_lines.append("%s x%d @ %s = %s" % (sku, quantity, _money(unit_cents), _money(amount_cents)))

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    tax_cents = tax.compute_tax(region, tax_lines, discount_pct)
    tax_pct = 0 if region is None else tax.tax_rate_pct(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out_lines.append("Subtotal: %s" % _money(subtotal_cents))
    out_lines.append("Discount (%s%%): -%s" % (_percent(discount_pct), _money(discount_cents)))
    out_lines.append("Tax (%s%%): %s" % (_percent(tax_pct), _money(tax_cents)))
    out_lines.append("Total: %s" % _money(total_cents))

    return "\n".join(out_lines)
