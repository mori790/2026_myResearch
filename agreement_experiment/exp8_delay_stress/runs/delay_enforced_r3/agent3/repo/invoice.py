"""Invoice module. Owned by agent3. Implement render_invoice(order).

Cross-module contracts (committed in the decision log):
  pricing.get_item(sku)          -> dict with price_cents (int), category (str), or None
  pricing.get_customer(cust_id)  -> dict with name (str), discount_pct (int, 10 = 10%),
                                    region (str), or None
  tax.compute_tax(lines, region, discount_pct) -> int cents
      lines = [{"category": str, "amount_cents": int}] for known skus, in order
      region None (unknown customer) -> 0
  tax.tax_pct(region) -> percent number (only called when region is not None)

All money is integer cents; percentages are percent numbers.
This module does no tax computation; it only applies the customer discount.
"""

import pricing
import tax


def _money(cents):
    """Format integer cents as dollars: 1250 -> '$12.50', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s$%d.%02d" % (sign, cents // 100, cents % 100)


def _percent(value):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = repr(float(value))
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _round_half_up_div(numerator, denominator):
    """Integer division rounding half up (numerator, denominator >= 0)."""
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder >= denominator:
        quotient += 1
    return quotient


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax (region None -> tax 0).
        customer_label = customer_id
        discount_pct = 0
        region = None
    else:
        customer_label = customer["name"]
        discount_pct = customer["discount_pct"]
        region = customer["region"]

    out = ["Customer: %s" % customer_label]

    tax_lines = []      # known skus only, in order; tax.py decides exemption by category
    subtotal_cents = 0

    for sku, quantity in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: %s" % sku)
            continue

        unit_cents = item["price_cents"]
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        tax_lines.append({"category": item["category"], "amount_cents": amount_cents})
        out.append("%s x%d @ %s = %s" % (sku, quantity, _money(unit_cents), _money(amount_cents)))

    # Customer discount: subtotal * percent / 100, rounded to the cent, half up.
    discount_cents = _round_half_up_div(subtotal_cents * discount_pct, 100)

    # Tax amount and tax percent come from tax.py only.
    tax_cents = tax.compute_tax(tax_lines, region, discount_pct)
    tax_percent = tax.tax_pct(region) if region is not None else 0

    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: %s" % _money(subtotal_cents))
    out.append("Discount (%s%%): -%s" % (_percent(discount_pct), _money(discount_cents)))
    out.append("Tax (%s%%): %s" % (_percent(tax_percent), _money(tax_cents)))
    out.append("Total: %s" % _money(total_cents))

    return "\n".join(out)
