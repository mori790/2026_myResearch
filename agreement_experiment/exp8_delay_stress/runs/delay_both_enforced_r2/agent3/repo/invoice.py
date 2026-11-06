"""Invoice rendering (owned by agent3).

Built on the committed team decisions:
- money_unit (v4): money is decimal.Decimal in dollars, quantized to 0.01, ROUND_HALF_UP.
- percent_unit (v3): percents are plain numbers (10 means 10%).
- not_found_signal (v3): pricing lookups return None on a miss; the caller checks.
- pricing_api (v3): pricing.get_item(sku) -> dict | None   (keys: sku, name, price, category)
                    pricing.get_customer(id) -> dict | None (keys: id, name, discount, region)
- tax_interface (v6): tax.compute_tax(region, taxable_lines, discount_pct) -> Decimal tax amount
                      tax.rate_pct(region) -> Decimal percent number (8.25 means 8.25%)

invoice.py does no tax rule computation: all tax logic lives in tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
ZERO = Decimal("0")
HUNDRED = Decimal("100")


def _money(amount):
    """Quantize a Decimal dollar amount to the cent (half up)."""
    return Decimal(str(amount)).quantize(CENT, rounding=ROUND_HALF_UP)


def _money_text(amount):
    """Format a Decimal dollar amount as '$12.50' (amount must already be in cents)."""
    return "$" + format(_money(amount), ".2f")


def _percent_text(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0.00 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    """Render an invoice for order = {"customer": id, "lines": [[sku, qty], ...]}.

    Returns the invoice text with lines joined by "\\n" and no trailing newline.
    """
    customer_id = order["customer"]

    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (per the spec).
        name = customer_id
        discount_pct = ZERO
        region = None
    else:
        name = customer["name"]
        discount_pct = Decimal(str(customer["discount"]))
        region = customer["region"]

    output = [f"Customer: {name}"]
    subtotal = ZERO
    taxable_lines = []  # (category, line_amount) for every known line; tax.py filters them

    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output.append(f"UNKNOWN SKU: {sku}")
            continue

        unit_price = Decimal(str(item["price"]))
        line_amount = _money(unit_price * qty)
        subtotal += line_amount
        output.append(
            f"{sku} x{qty} @ {_money_text(unit_price)} = {_money_text(line_amount)}"
        )
        taxable_lines.append((item["category"], line_amount))

    subtotal = _money(subtotal)
    discount = _money(subtotal * discount_pct / HUNDRED)

    # tax.py decides the taxable base and the rate; region None -> tax 0.00.
    tax_amount = _money(tax.compute_tax(region, taxable_lines, discount_pct))
    if region is None:
        tax_pct = ZERO
    else:
        tax_pct = Decimal(str(tax.rate_pct(region)))

    total = _money(subtotal - discount + tax_amount)

    output.append(f"Subtotal: {_money_text(subtotal)}")
    output.append(f"Discount ({_percent_text(discount_pct)}%): -{_money_text(discount)}")
    output.append(f"Tax ({_percent_text(tax_pct)}%): {_money_text(tax_amount)}")
    output.append(f"Total: {_money_text(total)}")

    return "\n".join(output)
