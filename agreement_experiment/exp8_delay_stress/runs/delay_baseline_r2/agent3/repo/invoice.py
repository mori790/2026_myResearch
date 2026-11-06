"""Invoice module. Owned by agent3. Implement render_invoice(order).

All item, customer and tax data come from pricing.py and tax.py.
This module does not contain any tax rules.

Data conventions (agreed with agent1 in topic 'pricing_api'):
  - pricing.get_item(sku)       -> dict {sku, name, price (float dollars), category} or None
  - pricing.get_customer(id)    -> dict {id, name, discount (fraction, 0.10 = 10% off), region} or None
  - tax.compute_tax(lines, region, discount) -> float dollars (see _tax_amount)
  - tax.get_tax_rate(region)    -> fraction (0.0825 = 8.25%) or None

Money arithmetic is done with Decimal, rounded to the cent (ROUND_HALF_UP).
Floats from pricing/tax are converted with Decimal(str(x)) to avoid binary noise.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dec(value):
    """Convert a float (or int/str) from another module to Decimal without binary noise."""
    return Decimal(str(value))


def _quantize(amount):
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal dollar amount, e.g. Decimal('25') -> '$25.00', Decimal('-3.91') -> '-$3.91'."""
    value = _quantize(amount)
    if value < 0:
        return "-$" + format(-value, "f")
    return "$" + format(value, "f")


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros, e.g. 0.1 -> '10', 0.0825 -> '8.25', 0 -> '0'."""
    percent = _dec(fraction) * 100
    return format(percent.normalize(), "f")


def _lookup_customer(customer_id):
    """Return (name, region, discount_fraction) for a customer.

    Unknown customers are shown by their id, with no region (so no tax) and 0% discount.
    """
    customer = pricing.get_customer(customer_id)
    if customer is None:
        return customer_id, None, 0.0
    name = customer.get("name") or customer_id
    return name, customer.get("region"), customer.get("discount") or 0.0


def _tax_amount(priced_lines, region, discount_fraction):
    """Tax amount in dollars, as a Decimal rounded to the cent. Computed by tax.py."""
    return _quantize(_dec(tax.compute_tax(priced_lines, region, discount_fraction)))


def _tax_fraction(region):
    """Tax rate as a fraction, e.g. 0.0825. Zero when there is no region."""
    if region is None:
        return Decimal("0")
    rate = tax.get_tax_rate(region)
    return _dec(rate) if rate is not None else Decimal("0")


def render_invoice(order):
    customer_id = order["customer"]
    name, region, discount_fraction = _lookup_customer(customer_id)

    out = [f"Customer: {name}"]
    priced_lines = []  # (category, amount in dollars) for known SKUs only; used by tax.py
    subtotal = Decimal("0")

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _dec(item["price"])
        amount = _quantize(unit_price * quantity)
        subtotal += amount
        priced_lines.append((item.get("category", ""), float(amount)))
        out.append(f"{sku} x{quantity} @ {_money(unit_price)} = {_money(amount)}")

    subtotal = _quantize(subtotal)
    discount = _quantize(subtotal * _dec(discount_fraction))
    tax_amount = _tax_amount(priced_lines, region, discount_fraction)
    tax_rate = _tax_fraction(region)
    total = _quantize(subtotal - discount + tax_amount)

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_fraction)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_rate)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")

    return "\n".join(out)
