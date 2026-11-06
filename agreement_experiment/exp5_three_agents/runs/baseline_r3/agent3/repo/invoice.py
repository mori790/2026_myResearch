"""Invoice module. Owned by agent3.

render_invoice(order) gets all item, customer and tax information from
pricing.py (agent1) and tax.py (agent2). It does not compute tax rules itself.

Interfaces used (agreed in the 'api_interface' topic of the agreement log):
  pricing.get_item(sku)           -> Item(sku, name, price_cents, category) or None/KeyError
  pricing.get_customer(id)        -> Customer(id, name, discount_pct, region) or None/KeyError
  tax.tax_rate(region)            -> Decimal percent (e.g. 8.25); unknown region -> 0
  tax.compute_tax(region, discount_pct, lines) -> Decimal tax amount in dollars
                                     lines = [(Decimal amount, category), ...]

Money is kept in integer cents; percentages are Decimal.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _lookup(func, key):
    """Call a pricing lookup, treating both None and KeyError as 'not found'."""
    try:
        return func(key)
    except KeyError:
        return None


def _round_to_int(value):
    """Round a Decimal to an integer, half up (value is in cents)."""
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _money(cents):
    """Format integer cents as $X.YY, with a leading '-' for negative amounts."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a Decimal percent without trailing zeros: 10, 8.25, 0."""
    text = format(Decimal(value), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _customer_fields(customer_id):
    """Return (name, discount_pct, region) for a customer; unknown -> (id, None, None)."""
    customer = _lookup(pricing.get_customer, customer_id)
    if customer is None:
        return customer_id, None, None
    name = getattr(customer, "name", customer_id)
    discount_pct = getattr(customer, "discount_pct", None)
    if discount_pct is None:
        discount_pct = getattr(customer, "discount_percent", None)
    region = getattr(customer, "region", None)
    if region is None and hasattr(pricing, "get_customer_region"):
        region = _lookup(pricing.get_customer_region, customer_id)
    return name, discount_pct, region


def render_invoice(order):
    customer_id = order["customer"]
    name, discount_pct, region = _customer_fields(customer_id)

    lines_out = [f"Customer: {name}"]

    # Known lines: (Decimal dollar amount, category) for tax.py.
    tax_lines = []
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = _lookup(pricing.get_item, sku)
        if item is None:
            lines_out.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_cents = int(item.price_cents)
        amount_cents = unit_cents * int(quantity)
        subtotal_cents += amount_cents
        lines_out.append(
            f"{sku} x{quantity} @ {_money(unit_cents)} = {_money(amount_cents)}"
        )
        tax_lines.append((Decimal(amount_cents) / 100, item.category))  # dollars, per tax.py

    # Discount: subtotal * pct / 100, rounded half up to the cent.
    pct = Decimal(discount_pct) if discount_pct is not None else Decimal("0")
    discount_cents = _round_to_int(Decimal(subtotal_cents) * pct / 100)

    # Tax: entirely from tax.py (agent2). Unknown region -> rate 0 and tax 0.
    # Note: compute_tax applies the discount itself (taxable_base), so pass pct.
    rate = Decimal(tax.tax_rate(region)) if region is not None else Decimal("0")
    tax_amount = tax.compute_tax(region, pct, tax_lines)
    tax_cents = _round_to_int(Decimal(tax_amount) * 100)

    total_cents = subtotal_cents - discount_cents + tax_cents

    lines_out.append(f"Subtotal: {_money(subtotal_cents)}")
    lines_out.append(f"Discount ({_percent(pct)}%): -{_money(discount_cents)}")
    lines_out.append(f"Tax ({_percent(rate)}%): {_money(tax_cents)}")
    lines_out.append(f"Total: {_money(total_cents)}")

    return "\n".join(lines_out)
