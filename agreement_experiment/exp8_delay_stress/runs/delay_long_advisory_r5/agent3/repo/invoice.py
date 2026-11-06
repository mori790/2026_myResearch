"""Invoice module. Owned by agent3. Implement render_invoice(order).

Agreed interfaces (committed in the shared decision log):
  money_representation v2   : integer cents (1250 = $12.50)
  percent_representation v2 : percent numbers (10 = 10%, 8.25 = 8.25%)
  pricing_api v2            : pricing.get_item(sku) -> Item|None  (sku, name, unit_price [cents], category)
                              pricing.get_customer(id) -> Customer|None (id, name, discount_pct, region)
  tax-interface v3          : tax.compute_tax(region, discount_pct, lines) -> int cents
                              lines = [(category, amount_cents), ...]; region None -> 0 tax
                              tax.tax_percent(region) -> float percent

Invoice does not compute the tax base or any tax rule. It only computes the
displayed discount amount (subtotal * discount_pct, rounded half up), which the
invoice format requires.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format a non-negative integer amount in cents as $X.YY."""
    return f"${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a percent number without trailing zeros (10 -> '10', 8.25 -> '8.25')."""
    text = f"{Decimal(str(value)):f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _discount_cents(subtotal_cents, discount_pct):
    """Discount amount in cents: subtotal * percent / 100, rounded half up."""
    value = Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (tax.py gives 0 for region None).
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer.name
        discount_pct = customer.discount_pct
        region = customer.region

    lines_out = [f"Customer: {customer_name}"]
    priced_lines = []  # (category, amount_cents) for known items, passed to tax.py
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            lines_out.append(f"UNKNOWN SKU: {sku}")
            continue
        amount_cents = item.unit_price * quantity
        subtotal_cents += amount_cents
        priced_lines.append((item.category, amount_cents))
        lines_out.append(
            f"{sku} x{quantity} @ {_money(item.unit_price)} = {_money(amount_cents)}"
        )

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    tax_cents = tax.compute_tax(region, discount_pct, priced_lines)
    tax_pct = tax.tax_percent(region) if region is not None else 0
    total_cents = subtotal_cents - discount_cents + tax_cents

    lines_out.append(f"Subtotal: {_money(subtotal_cents)}")
    lines_out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount_cents)}")
    lines_out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_cents)}")
    lines_out.append(f"Total: {_money(total_cents)}")

    return "\n".join(lines_out)
