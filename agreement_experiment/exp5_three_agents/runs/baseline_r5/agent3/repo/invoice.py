"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the agreed interfaces:
  pricing.get_item(sku) -> Item(sku, name, price_cents, category); KeyError if unknown
  pricing.get_customer(customer_id) -> Customer(id, name, discount_pct, region); KeyError if unknown
  tax.tax_breakdown(lines, region, discount_pct=0) -> dict with "tax" (cents) and "tax_pct" (percent)
  tax.compute_tax(lines, region, discount_pct=0) -> Decimal amount (tax.py owns all tax rules)

Money is handled as integer cents. Percents are decimal.Decimal.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as $X.YY, with a leading minus sign if negative."""
    sign = "-" if cents < 0 else ""
    cents = abs(int(cents))
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _dollars(cents):
    """Integer cents -> exact dollar string, e.g. 2500 -> '25.00'."""
    return f"{cents // 100}.{cents % 100:02d}"


def _to_cents(dollars):
    """Dollar amount (Decimal, str, or number) -> integer cents, rounded half up."""
    exact = Decimal(str(dollars)) * 100
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _percent(value):
    """Format a percent without trailing zeros: 10, 8.25, 0."""
    text = format(Decimal(str(value)), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _discount_cents(subtotal_cents, discount_pct):
    """subtotal * discount_pct / 100, rounded to the cent, half up."""
    exact = Decimal(subtotal_cents) * Decimal(discount_pct) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    try:
        customer = pricing.get_customer(customer_id)
        customer_name = customer.name
        discount_pct = customer.discount_pct
        region = customer.region
    except KeyError:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_pct = 0
        region = None

    out = [f"Customer: {customer_name}"]
    priced_lines = []  # (sku, quantity, line_cents, category) for known SKUs only
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        line_cents = item.price_cents * quantity
        subtotal_cents += line_cents
        priced_lines.append((sku, quantity, line_cents, item.category))
        out.append(f"{sku} x{quantity} @ {_money(item.price_cents)} = {_money(line_cents)}")

    # tax.py takes line amounts in dollars (as exact strings) and returns dollars.
    tax_lines = [(category, _dollars(line_cents)) for _, _, line_cents, category in priced_lines]
    breakdown = tax.tax_breakdown(tax_lines, region, discount_pct)
    tax_cents = _to_cents(breakdown["tax"])
    tax_pct = breakdown["tax_pct"]

    discount_cents = _discount_cents(subtotal_cents, discount_pct)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append(f"Subtotal: {_money(subtotal_cents)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount_cents)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_cents)}")
    out.append(f"Total: {_money(total_cents)}")
    return "\n".join(out)
