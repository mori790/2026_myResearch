"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed team APIs:
  pricing.get_item(sku)            -> {sku, name, price, category} or None
  pricing.get_customer(id)         -> {id, name, discount, region} or None
  tax.compute_tax(lines, customer) -> float dollars (tax only, not added to total)
  tax.get_tax_rate(region)         -> fraction or None
Money crossing module boundaries is float dollars (committed money_unit);
percentages are fractions (committed percent_unit).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _dec(value):
    """Convert a float value to Decimal using its shortest repr (avoids 0.1 artefacts)."""
    return Decimal(str(value))


def _round_cent(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(value):
    """Format a non-negative Decimal as $X.YY."""
    return "$" + str(_round_cent(value))


def _percent(fraction):
    """Format a fraction as a percent without trailing zeros: 0.1 -> '10', 0.0825 -> '8.25'."""
    pct = _dec(fraction) * 100
    return format(pct.normalize(), "f")


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_rate = Decimal("0")
        tax_rate = Decimal("0")
    else:
        customer_name = customer["name"]
        discount_rate = _dec(customer["discount"])
        rate = tax.get_tax_rate(customer["region"])
        if rate is None:
            # Same policy as tax.py: never silently charge 0% for a known customer.
            raise ValueError("no tax rate for region %r" % customer["region"])
        tax_rate = _dec(rate)

    out = ["Customer: " + str(customer_name)]
    subtotal = Decimal("0")
    tax_lines = []

    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: %s" % sku)
            continue
        unit_price = _dec(item["price"])
        amount = unit_price * qty
        subtotal += amount
        out.append("%s x%s @ %s = %s" % (
            sku, qty, _money(unit_price), _money(amount)))
        tax_lines.append({"category": item["category"], "amount": float(amount)})

    discount = _round_cent(subtotal * discount_rate)

    # tax.py applies the customer's discount to the taxable base itself.
    tax_amount = _round_cent(_dec(tax.compute_tax(tax_lines, customer)))

    total = subtotal - discount + tax_amount

    out.append("Subtotal: " + _money(subtotal))
    out.append("Discount (%s%%): -%s" % (_percent(discount_rate), _money(discount)))
    out.append("Tax (%s%%): %s" % (_percent(tax_rate), _money(tax_amount)))
    out.append("Total: " + _money(total))

    return "\n".join(out)
