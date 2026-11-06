"""Invoice module. Owned by agent3. Implement render_invoice(order).

Follows the committed team decisions:
  MONEY_REPRESENTATION v2: money is int cents; percents are int thousandths
                           of a percent (10% = 10000, 8.875% = 8875).
  module_api v2:           pricing.get_item(sku) -> {"sku", "name", "category",
                           "unit_price_cents"} or None;
                           pricing.get_customer(cid) -> {"id", "name", "region",
                           "discount_pm"} or None.
  TAX_API v2:              tax.compute(region, lines, discount_pm) -> (rate_pm, tax_cents),
                           lines = [(category, amount_cents), ...].

Tax rules (exemptions, rates, rounding of the tax itself) live in tax.py only.
"""

import pricing
import tax

PM_PER_WHOLE = 100000  # 100% in thousandths of a percent


def _money(cents):
    """Format integer cents as dollars, e.g. 3910 -> '$39.10', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(pm):
    """Format thousandths of a percent without trailing zeros.

    8250 -> '8.25', 10000 -> '10', 8875 -> '8.875', 0 -> '0'.
    """
    whole, frac = divmod(pm, 1000)
    if frac == 0:
        return str(whole)
    return f"{whole}.{frac:03d}".rstrip("0")


def _round_half_up_div(numerator, denominator):
    """Integer division rounding half up (for non-negative values)."""
    return (numerator + denominator // 2) // denominator


def render_invoice(order):
    customer_id = order["customer"]
    customer = pricing.get_customer(customer_id)
    if customer is None:
        # Unknown customer: shown by id, 0% discount, no region (so tax.py gives 0%).
        name = customer_id
        region = None
        discount_pm = 0
    else:
        name = customer["name"]
        region = customer["region"]
        discount_pm = customer["discount_pm"]

    out = [f"Customer: {name}"]
    subtotal = 0
    tax_lines = []  # (category, amount_cents) for known items only
    for sku, qty in order["lines"]:
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit = item["unit_price_cents"]
        amount = unit * qty
        subtotal += amount
        tax_lines.append((item["category"], amount))
        out.append(f"{sku} x{qty} @ {_money(unit)} = {_money(amount)}")

    discount = _round_half_up_div(subtotal * discount_pm, PM_PER_WHOLE)
    tax_pm, tax_cents = tax.compute(region, tax_lines, discount_pm)
    total = subtotal - discount + tax_cents

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_pm)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_pm)}%): {_money(tax_cents)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
