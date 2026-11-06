"""Invoice module. Owned by agent3. Implement render_invoice(order).

Depends on:
  pricing.get_item(sku)       -> Item with .price_cents (int) and .category, or None
  pricing.get_customer(id)    -> Customer with .name, .discount_pct (int percent), .region, or None
  tax.compute_tax(lines, region, discount_pct) -> int cents
      lines = [(category, amount_cents), ...]; region None means no tax
  tax.tax_rate_pct(region)    -> Decimal percent (e.g. 8.25)

Money is decimal.Decimal in dollars internally. Cents are converted only at
the boundary with tax.py. Tax rules are not computed here.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _to_dollars(cents):
    """Integer cents -> Decimal dollars (1250 -> Decimal('12.50'))."""
    return (Decimal(cents) / 100).quantize(CENT, rounding=ROUND_HALF_UP)


def _to_cents(dollars):
    """Decimal dollars -> integer cents, rounded half up."""
    return int((dollars * 100).to_integral_value(rounding=ROUND_HALF_UP))


def _money(amount):
    """Decimal dollars -> '$12.50'."""
    return "$" + str(amount.quantize(CENT, rounding=ROUND_HALF_UP))


def _pct(value):
    """Percent number -> text without trailing zeros (10 -> '10', 8.25 -> '8.25', 0 -> '0')."""
    return format(Decimal(value).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer.name
        discount_pct = customer.discount_pct
        region = customer.region

    out = [f"Customer: {customer_name}"]
    subtotal = Decimal("0.00")
    taxable_lines = []  # (category, amount_cents) pairs for tax.py

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _to_dollars(item.price_cents)
        amount = unit_price * qty
        subtotal += amount
        taxable_lines.append((item.category, _to_cents(amount)))
        out.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}")

    discount = (subtotal * Decimal(discount_pct) / 100).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_amount = _to_dollars(tax.compute_tax(taxable_lines, region, discount_pct))
    tax_pct = Decimal(tax.tax_rate_pct(region)) if region is not None else Decimal(0)

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_pct(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({_pct(tax_pct)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")

    return "\n".join(out)
