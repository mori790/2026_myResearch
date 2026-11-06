"""Invoice module. Owned by agent3. Implement render_invoice(order).

Boundaries (committed in agree.py):
  pricing.get_item(sku)       -> {"sku", "name", "unit_price_cents": int, "category"} or None
  pricing.get_customer(cid)   -> {"id", "name", "discount_pct": number, "region": str} or None
  tax.compute_tax(region, discount_pct, lines) -> int cents
      lines = [{"category": str, "amount_cents": int}], region None -> 0
  tax.tax_pct(region)         -> number (percent), KeyError if region unknown

Internal convention (team standard): money as decimal.Decimal dollars,
percent as multiplier, lookup miss -> default value. This module does not
compute tax rules; it only calls tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Integer cents -> Decimal dollars, formatted with 2 decimals."""
    dollars = (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))
    return f"{dollars:.2f}"


def _percent(value):
    """Percent number -> text without trailing zeros (10 -> '10', 8.25 -> '8.25', 0 -> '0')."""
    text = format(Decimal(str(value)).normalize(), "f")
    return text


def _lookup_customer(customer_id):
    """Unknown customer: shown by id, 0% discount, 0% tax (region None)."""
    customer = pricing.get_customer(customer_id)
    if customer is None:
        return {"name": customer_id, "discount_pct": 0, "region": None}
    return {
        "name": customer.get("name") or customer_id,
        "discount_pct": customer.get("discount_pct", 0),
        "region": customer.get("region"),
    }


def render_invoice(order):
    customer = _lookup_customer(order.get("customer", ""))
    discount_pct = customer["discount_pct"]
    region = customer["region"]

    output = [f"Customer: {customer['name']}"]
    line_items = []   # [{"category", "amount_cents"}] for tax.py
    subtotal_cents = 0

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            output.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_cents = item["unit_price_cents"]
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        line_items.append({"category": item.get("category", ""), "amount_cents": amount_cents})
        output.append(
            f"{sku} x{quantity} @ ${_money(unit_cents)} = ${_money(amount_cents)}"
        )

    # Discount: subtotal * percent / 100, rounded to the cent, half up.
    discount_cents = int(
        (Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100))
        .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    # Tax comes entirely from tax.py (taxability, rates, rounding).
    tax_cents = tax.compute_tax(region, discount_pct, line_items)
    tax_percent = 0 if region is None else tax.tax_pct(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    output.append(f"Subtotal: ${_money(subtotal_cents)}")
    output.append(f"Discount ({_percent(discount_pct)}%): -${_money(discount_cents)}")
    output.append(f"Tax ({_percent(tax_percent)}%): ${_money(tax_cents)}")
    output.append(f"Total: ${_money(total_cents)}")

    return "\n".join(output)
