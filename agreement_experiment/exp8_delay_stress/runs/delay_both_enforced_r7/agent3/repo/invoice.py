"""Invoice module. Owned by agent3. Implement render_invoice(order).

All item, customer and tax information comes from pricing.py and tax.py.
This module does not compute tax rules itself.

Committed team APIs used here (see agreement log: pricing_interface v1, tax_interface v3):
  pricing.get_item(sku) -> dict {sku, name, price (float dollars), category} or None
  pricing.get_customer(customer_id) -> dict {id, name, discount (float fraction, 0.10),
                                             region (state code)} or None
  tax.compute_tax(region, lines, discount) -> float dollars, rounded half up to the cent
      lines = [(line_amount float dollars, category)], known items only, before discount/tax
      discount = fraction (0.10 means 10%); tax.py applies it to the taxable amount
      region None -> 0 tax
  tax.tax_rate(region) -> float fraction (0.0825); None -> 0.0

Inside this module, money is decimal.Decimal in dollars (team standard).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ZERO = Decimal("0")


def _dec(value):
    """Convert a float/str/int from another module to an exact Decimal."""
    return Decimal(str(value))


def _cents(amount):
    """Round a Decimal amount to the cent, half up."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal dollar amount as '$12.50' (absolute value; sign added by caller)."""
    return "$" + format(_cents(abs(amount)), "f")


def _percent(fraction):
    """Format a fraction as a percent number without trailing zeros: 0.10 -> '10', 0.0825 -> '8.25'."""
    value = (_dec(fraction) * 100).normalize()
    text = format(value, "f")
    return "0" if text in ("-0", "") else text


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax
        name = customer_id
        discount_fraction = ZERO
        region = None
    else:
        name = customer.get("name") or customer_id
        discount_fraction = _dec(customer.get("discount", 0))
        region = customer.get("region")

    output = [f"Customer: {name}"]

    # Line items in order. Unknown SKUs are listed in place and skipped in all totals.
    tax_lines = []  # (line_amount, category) for known SKUs only
    subtotal = ZERO
    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            output.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = _cents(_dec(item["price"]))
        line_amount = unit_price * quantity
        subtotal += line_amount
        tax_lines.append((float(line_amount), item.get("category", "")))
        output.append(f"{sku} x{quantity} @ {_money(unit_price)} = {_money(line_amount)}")

    # Discount: subtotal * discount fraction, rounded to the cent (half up).
    discount = _cents(subtotal * discount_fraction)

    # Tax amount and tax rate come from tax.py (tax.py applies the discount to taxable lines).
    tax_amount = _cents(_dec(tax.compute_tax(region, tax_lines, float(discount_fraction))))
    tax_rate = tax.tax_rate(region) if region is not None else 0.0

    total = subtotal - discount + tax_amount

    output.append(f"Subtotal: {_money(subtotal)}")
    output.append(f"Discount ({_percent(discount_fraction)}%): -{_money(discount)}")
    output.append(f"Tax ({_percent(tax_rate)}%): {_money(tax_amount)}")
    output.append(f"Total: {_money(total)}")

    return "\n".join(output)
