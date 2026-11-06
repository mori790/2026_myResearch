"""Invoice module. Owned by agent3. Implement render_invoice(order).

All item, customer and tax information comes from pricing.py and tax.py.
This module does no tax rule computation itself.

Committed decisions followed (see agree.py lookup):
  MONEY_UNIT: pricing and tax return float dollars (12.5 == $12.50).
  PERCENT_UNIT: percents are fractions (0.10 == 10%).
  NOT_FOUND: pricing/tax lookups return None when nothing matches.
  PRICING_API / TAX_API: see the committed interface.
  TAX_UNKNOWN_REGION: compute_tax raises KeyError for a known customer whose
      region has no tax row; this module reports that case as ValueError.
  INVOICE_UNKNOWN_REGION: render_invoice raises ValueError for that case.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dec(value):
    """Convert a float dollar/fraction value to Decimal via its shortest repr."""
    return Decimal(repr(float(value)))


def _round_cent(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(value):
    """Format a Decimal as dollars with two decimals, e.g. $25.00 or -$3.91."""
    value = _round_cent(value)
    if value < 0:
        return "-$" + format(-value, ".2f")
    return "$" + format(value, ".2f")


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros, e.g. 0.0825 -> 8.25%."""
    pct = (_dec(fraction) * 100).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    return format(pct.normalize(), "f") + "%"


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_label = customer_id
        discount_fraction = Decimal("0")
        tax_fraction = Decimal("0")
        tax_customer = None
    else:
        customer_label = customer.get("name", customer_id)
        discount_fraction = _dec(customer.get("discount", 0))
        region = customer.get("region", "")
        rate = tax.get_tax_rate(region)
        if rate is None:
            raise ValueError(
                "no tax rate for customer %r in region %r" % (customer_id, region)
            )
        tax_fraction = _dec(rate)
        tax_customer = customer

    out_lines = ["Customer: %s" % customer_label]
    tax_lines = []
    subtotal = Decimal("0")

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: %s" % sku)
            continue
        unit_price = _dec(item["unit_price"])
        amount = _round_cent(unit_price * quantity)
        subtotal += amount
        out_lines.append(
            "%s x%d @ %s = %s" % (sku, quantity, _money(unit_price), _money(amount))
        )
        tax_lines.append({"category": item.get("category", ""), "amount": float(amount)})

    subtotal = _round_cent(subtotal)
    discount = _round_cent(subtotal * discount_fraction)

    if tax_customer is None:
        tax_amount = Decimal("0")
    else:
        tax_amount = _round_cent(_dec(tax.compute_tax(tax_customer, tax_lines)))

    total = subtotal - discount + tax_amount

    out_lines.append("Subtotal: %s" % _money(subtotal))
    out_lines.append("Discount (%s): -%s" % (_percent(discount_fraction), _money(discount)))
    out_lines.append("Tax (%s): %s" % (_percent(tax_fraction), _money(tax_amount)))
    out_lines.append("Total: %s" % _money(total))

    return "\n".join(out_lines)
