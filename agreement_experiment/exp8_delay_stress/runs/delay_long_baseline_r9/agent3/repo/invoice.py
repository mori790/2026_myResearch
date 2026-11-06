"""Invoice module. Owned by agent3. Implement render_invoice(order).

Interfaces used (agreed in topics pricing_api v3 and tax_api v1):
  pricing.get_item(sku)          -> dict {sku, name, price, price_cents, category} or None
  pricing.get_customer(cid)      -> dict {id, name, discount, discount_pct, region} or None
  tax.tax_rate(region)           -> float percent (8.25 means 8.25%); 0 for None
  tax.compute_tax(lines, region, discount_pct) -> int cents
      lines = [(category, amount_cents)], undiscounted; exempt categories excluded by tax.py

Money is handled as decimal.Decimal dollars in this module. Integer cents coming
from pricing/tax are converted at the boundary. Tax rules are not computed here.
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _dollars(cents):
    """Integer cents -> Decimal dollars."""
    return Decimal(int(cents)) / HUNDRED


def _money(amount):
    """Decimal dollars -> '$12.50' (rounded half up to the cent)."""
    cents = Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP)
    return "$" + format(cents, "f")


def _percent(value):
    """Percent number -> text without trailing zeros: 10 -> '10%', 8.25 -> '8.25%'."""
    text = format(Decimal(str(value)).normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text + "%"


def render_invoice(order):
    customer_id = order.get("customer", "")
    lines_in = order.get("lines", [])

    customer = pricing.get_customer(customer_id)
    if customer is None:
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer.get("name") or customer_id
        discount_pct = customer.get("discount_pct", 0)
        region = customer.get("region")

    out = [f"Customer: {customer_name}"]
    subtotal_cents = 0
    taxable_lines = []  # (category, undiscounted amount_cents) for tax.py

    for sku, qty in lines_in:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = int(item["price_cents"])
        amount_cents = unit_cents * int(qty)
        subtotal_cents += amount_cents
        out.append(
            f"{sku} x{qty} @ {_money(_dollars(unit_cents))} = {_money(_dollars(amount_cents))}"
        )
        taxable_lines.append((item.get("category", ""), amount_cents))

    subtotal = _dollars(subtotal_cents)
    discount = (subtotal * Decimal(str(discount_pct)) / HUNDRED).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    tax_cents = tax.compute_tax(taxable_lines, region, discount_pct)
    tax_amount = _dollars(tax_cents)
    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_pct)}): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax.tax_rate(region))}): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
