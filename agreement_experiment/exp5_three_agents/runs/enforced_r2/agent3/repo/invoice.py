"""Invoice module. Owned by agent3. Implement render_invoice(order).

Depends on the committed decisions pricing_api v1, tax_api v1 and invoice-api v3:

  pricing.get_item(sku)                          -> Item(sku, name, price_cents, category); KeyError if unknown
  pricing.line_total_cents(sku, qty)             -> int
  pricing.get_customer(cid)                      -> Customer(id, name, discount_pct, region); KeyError if unknown
  pricing.discount_cents(subtotal, cid)          -> int (half up, 0 for 0%)
  tax.calculate_tax(region, discount_pct, lines) -> (tax_cents, tax_pct: Decimal)
      lines = [(category, line_total_cents), ...] for known SKUs only

This module owns only line amounts, subtotal, discount line, total and text
formatting. It does not decide taxability or tax rates.
"""

from decimal import Decimal

import pricing
import tax


def _money(cents):
    """Format integer cents as a dollar amount, e.g. 1250 -> '$12.50', -391 -> '-$3.91'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def _percent(value):
    """Format a percent without trailing zeros: 10 -> '10', Decimal('8.250') -> '8.25'."""
    return format(Decimal(value).normalize(), "f")


def render_invoice(order):
    customer_id = order["customer"]

    # Unknown customers are shown by id, with 0% discount and region None (0% tax).
    try:
        customer = pricing.get_customer(customer_id)
    except KeyError:
        customer = None

    if customer is None:
        customer_name = customer_id
        discount_pct = 0
        region = None
    else:
        customer_name = customer.name
        discount_pct = customer.discount_pct
        region = customer.region

    out = [f"Customer: {customer_name}"]

    subtotal = 0
    tax_lines = []  # (category, line_total_cents) for known SKUs only

    for sku, qty in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except KeyError:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        line_total = pricing.line_total_cents(sku, qty)
        out.append(f"{sku} x{qty} @ {_money(item.price_cents)} = {_money(line_total)}")
        subtotal += line_total
        tax_lines.append((item.category, line_total))

    if customer is None:
        discount = 0
    else:
        discount = pricing.discount_cents(subtotal, customer_id)

    # tax.py applies the discount only to taxable lines, so we pass the undiscounted lines.
    tax_cents, tax_pct = tax.calculate_tax(region, discount_pct, tax_lines)

    total = subtotal - discount + tax_cents

    out.append(f"Subtotal: {_money(subtotal)}")
    # The discount line always shows a minus sign, even for zero: "Discount (0%): -$0.00".
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_cents)}")
    out.append(f"Total: {_money(total)}")

    return "\n".join(out)
