"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the team APIs:
  pricing.get_item(sku) -> dict {sku, name, price (float dollars), category} or None
  pricing.get_customer(id) -> dict {id, name, discount (float fraction), region} or None
  tax.compute_tax(region, lines, discount_pct=0) -> int cents
      lines = [(category, amount_cents), ...] for known skus only
  tax.tax_pct(region) -> Decimal percent (None region gives 0)
Tax rules are not implemented here; invoice.py only does formatting and
subtotal/discount/total arithmetic in Decimal dollars.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _money(amount):
    """Round a Decimal dollar amount to the cent, half up."""
    return Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP)


def _money_text(amount):
    """Two-decimal dollar text, e.g. Decimal('12.5') -> '12.50'."""
    return f"{_money(amount):.2f}"


def _percent_text(value):
    """Percent text without trailing zeros: 10.00 -> '10', 8.2500 -> '8.25', 0 -> '0'."""
    text = format(Decimal(value).normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text if text else "0"


def _dec(value):
    """Convert a float (or int/str) money or fraction value to Decimal without binary noise."""
    return Decimal(str(value))


def render_invoice(order):
    customer = pricing.get_customer(order["customer"])
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region=None).
        customer_label = order["customer"]
        region = None
        discount_pct = Decimal("0")
    else:
        customer_label = customer.get("name") or customer["id"]
        region = customer.get("region")
        discount_pct = _dec(customer.get("discount", 0)) * HUNDRED

    output_lines = [f"Customer: {customer_label}"]
    tax_lines = []  # (category, amount_cents) for known skus only
    subtotal = Decimal("0")

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = _dec(item["price"])
        amount = _money(unit * quantity)
        subtotal += amount
        tax_lines.append((item.get("category", ""), int(amount * 100)))
        output_lines.append(
            f"{sku} x{quantity} @ ${_money_text(unit)} = ${_money_text(amount)}"
        )

    subtotal = _money(subtotal)
    discount = _money(subtotal * discount_pct / HUNDRED)

    # tax.py applies the discount to the taxable total itself and returns integer cents.
    tax_cents = tax.compute_tax(region, tax_lines, float(discount_pct))
    tax_amount = Decimal(tax_cents) / 100
    tax_amount = _money(tax_amount)
    tax_pct = tax.tax_pct(region)
    tax_pct = Decimal(0) if tax_pct is None else _dec(tax_pct)

    total = _money(subtotal - discount + tax_amount)

    output_lines.append(f"Subtotal: ${_money_text(subtotal)}")
    output_lines.append(f"Discount ({_percent_text(discount_pct)}%): -${_money_text(discount)}")
    output_lines.append(f"Tax ({_percent_text(tax_pct)}%): ${_money_text(tax_amount)}")
    output_lines.append(f"Total: ${_money_text(total)}")

    return "\n".join(output_lines)
