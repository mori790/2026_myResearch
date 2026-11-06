"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed team decisions:
  - money-units:  all money amounts are integer cents (1250 = $12.50).
  - percent-units: percents are percent numbers (10 means 10%, 8.25 means 8.25%).
  - pricing_api v2:
      pricing.get_item(sku)           -> {sku, name, price_cents, category} or None
      pricing.get_customer(cust_id)   -> {id, name, discount_pct, region} or None
  - tax-api:
      tax.compute_tax(region, lines, discount_pct=0) -> int cents
          lines = [(category, gross_amount_cents), ...]; the discount is applied inside tax.py,
          so gross amounts are passed. region None means 0 tax.
      tax.tax_rate(region) -> Decimal percent (None -> 0).
  - unknown-customer-and-rounding: unknown customer pays 0 tax (region None); only the
      final tax is rounded (inside tax.py).

This module does not compute any tax rule itself. The discount is computed here:
discount = subtotal * discount_pct / 100, rounded to the cent, half up.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format a non-negative integer number of cents as dollars: 1250 -> '$12.50'."""
    return "${}.{:02d}".format(cents // 100, cents % 100)


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(value)).normalize(), "f")


def render_invoice(order):
    """Return the invoice text for an order as one string (lines joined with "\\n", no trailing newline).

    order = {"customer": "C1", "lines": [["A", 2], ["D", 2], ["Z", 1]]}  (sku, quantity)
    """
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None -> tax.py returns 0).
        customer_label = customer_id
        discount_pct = Decimal("0")
        region = None
    else:
        customer_label = customer["name"]
        discount_pct = Decimal(str(customer["discount_pct"]))
        region = customer["region"]

    output = ["Customer: " + customer_label]

    subtotal_cents = 0
    taxable_lines = []  # (category, gross_amount_cents) for tax.compute_tax
    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            output.append("UNKNOWN SKU: " + sku)
            continue
        unit_cents = item["price_cents"]
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        taxable_lines.append((item["category"], amount_cents))
        output.append("{} x{} @ {} = {}".format(sku, quantity, _money(unit_cents), _money(amount_cents)))

    # Discount: subtotal * percent / 100, rounded to the cent, half up.
    discount_exact = Decimal(subtotal_cents) * discount_pct / Decimal(100)
    discount_cents = int(discount_exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    # Tax comes from tax.py. It applies the discount itself, so gross amounts are passed.
    tax_cents = tax.compute_tax(region, taxable_lines, discount_pct)
    tax_percent = tax.tax_rate(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    output.append("Subtotal: " + _money(subtotal_cents))
    output.append("Discount ({}%): -{}".format(_percent(discount_pct), _money(discount_cents)))
    output.append("Tax ({}%): {}".format(_percent(tax_percent), _money(tax_cents)))
    output.append("Total: " + _money(total_cents))

    return "\n".join(output)
