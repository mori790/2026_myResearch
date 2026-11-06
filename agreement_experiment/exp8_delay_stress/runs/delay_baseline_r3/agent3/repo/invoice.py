"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the agreed APIs (agreement topic 'tax_api' and agent1's pricing API):
  pricing.get_item(sku)       -> Item | None      (Item.price: float dollars)
  pricing.get_customer(id)    -> Customer | None  (Customer.region: str, Customer.discount: float fraction)
  tax.compute_tax(lines, region, discount_pct=0) -> int cents
      lines: [{"amount_cents": int, "category": str}], region None = unknown customer -> 0 tax
  tax.tax_pct_for_region(region) -> float percent

Inside this module all money is decimal.Decimal in dollars; floats and cents
from the other modules are converted at this boundary only.
Tax rules (rates, exemptions) are NOT computed here.
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _dec(value):
    """Convert a float/int/str from another module to Decimal without float noise."""
    return Decimal(str(value))


def _money(amount):
    """Format a Decimal as $12.50 (rounded half up to the cent)."""
    return "$" + format(Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


def _signed_money(amount):
    """Format a Decimal as -$3.91 (always with a minus sign, as in the spec)."""
    return "-" + _money(abs(Decimal(amount)))


def _percent(value):
    """Format a percent without trailing zeros: 10, 8.25, 0."""
    text = format(Decimal(value).normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_label = customer_id
        region = None
        discount = Decimal("0")
    else:
        customer_label = customer.name or customer_id
        region = customer.region
        discount = _dec(customer.discount)  # fraction, 0.10 = 10%

    out = ["Customer: " + customer_label]
    subtotal = Decimal("0")
    tax_lines = []  # {"amount_cents": int, "category": str} for known skus only

    for item in order["lines"]:
        sku, qty = item[0], int(item[1])
        product = pricing.get_item(sku)
        if product is None:
            out.append("UNKNOWN SKU: " + sku)
            continue
        unit = _dec(product.price).quantize(CENT, rounding=ROUND_HALF_UP)
        amount = unit * qty
        subtotal += amount
        tax_lines.append({"amount_cents": int(amount * HUNDRED), "category": product.category})
        out.append(f"{sku} x{qty} @ {_money(unit)} = {_money(amount)}")

    discount_pct = float(discount * HUNDRED)
    discount_amount = (subtotal * discount).quantize(CENT, rounding=ROUND_HALF_UP)

    tax_cents = tax.compute_tax(tax_lines, region, discount_pct=discount_pct)
    tax_amount = (Decimal(tax_cents) / HUNDRED).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_percent = _dec(tax.tax_pct_for_region(region)) if region is not None else Decimal("0")

    total = subtotal - discount_amount + tax_amount

    out.append("Subtotal: " + _money(subtotal))
    out.append(f"Discount ({_percent(discount * HUNDRED)}%): {_signed_money(discount_amount)}")
    out.append(f"Tax ({_percent(tax_percent)}%): {_money(tax_amount)}")
    out.append("Total: " + _money(total))
    return "\n".join(out)
