"""Invoice module. Owned by agent3. Implement render_invoice(order).

Team standard: money is decimal.Decimal in dollars; percents are percent
numbers (10 = 10%); a lookup that finds nothing returns a default.

Committed decisions this module conforms to:
- pricing-api v1 (agent1): get_item(sku) -> dict {sku,name,price,category} or None,
  price is float dollars; get_customer(cust_id) -> dict {id,name,discount,region} or None,
  discount is a fraction (0.10 = 10%).
- tax-api v1 (agent2): get_tax_pct(region) -> float percent (8.25 = 8.25%),
  region None -> 0.0; compute_tax_cents(lines, region, discount_pct=0) -> int cents,
  lines = iterable of (category, amount_cents), amounts must be int,
  discount_pct is a percent number, region None -> 0 tax.

invoice.py never computes tax rules itself; all tax amounts come from tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")
ZERO = Decimal("0")


def _dec(value):
    """Convert a float/int/str from another module into an exact Decimal.

    Going through str() avoids binary-float artifacts (e.g. 0.1 -> 0.1, not 0.1000000000000000055...).
    """
    return Decimal(str(value))


def _money(amount):
    """Format a Decimal dollar amount as $12.50 (two decimals, rounded half up)."""
    return "$" + str(amount.quantize(CENT, rounding=ROUND_HALF_UP))


def _pct(value):
    """Format a percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(_dec(value).normalize(), "f")


def _pct_arg(value):
    """Pass a percent number to tax.py as int when integral, else as float."""
    d = _dec(value)
    if d == d.to_integral_value():
        return int(d)
    return float(d)


def _unit_cents(price):
    """Convert a float-dollar price from pricing.py to integer cents, half up."""
    return int((_dec(price) * HUNDRED).to_integral_value(rounding=ROUND_HALF_UP))


def render_invoice(order):
    """Return the invoice text for an order.

    order = {"customer": "C1", "lines": [["A", 2], ["D", 2], ["Z", 1]]}
    Unknown SKUs are listed as "UNKNOWN SKU: <sku>" and skipped.
    Unknown customers are shown by id, with 0% discount and 0% tax.
    """
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_name = customer_id
        discount_pct = ZERO  # percent number, 0 = 0%
        region = None  # tax.py: region None -> 0% tax
    else:
        customer_name = customer["name"]
        discount_pct = _dec(customer["discount"]) * HUNDRED  # fraction -> percent number
        region = customer["region"]

    out = [f"Customer: {customer_name}"]
    subtotal = Decimal("0.00")
    tax_lines = []  # (category, amount_cents) for tax.py

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_cents = _unit_cents(item["price"])
        line_cents = unit_cents * qty  # integer cents, sent to tax.py as-is
        line_amount = Decimal(line_cents).scaleb(-2)  # exact dollars, e.g. Decimal('25.00')
        subtotal += line_amount

        tax_lines.append((item["category"], line_cents))
        unit_price = _dec(item["price"]).quantize(CENT, rounding=ROUND_HALF_UP)
        out.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(line_amount)}")

    # Discount: subtotal * percent, rounded to the cent (half up).
    discount = (subtotal * discount_pct / HUNDRED).quantize(CENT, rounding=ROUND_HALF_UP)

    # Tax: computed entirely by tax.py (exemptions, rates, rounding, discount base).
    tax_cents = tax.compute_tax_cents(tax_lines, region, _pct_arg(discount_pct))
    tax_amount = Decimal(tax_cents).scaleb(-2)
    tax_pct = _dec(tax.get_tax_pct(region))

    total = subtotal - discount + tax_amount

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_pct(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({_pct(tax_pct)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")

    return "\n".join(out)
