"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses the committed APIs:
  pricing-api v1: get_item(sku) -> {sku, name, price (float dollars), category} or None;
                  get_customer(id) -> {id, name, discount (float fraction), region} or None.
  tax-api v1:     compute_tax_cents(lines, region, discount_pct) -> int cents;
                  get_tax_pct(region) -> percent number (8.25), 0.0 for None.

Money is handled as integer cents internally (Decimal for conversions and rounding),
and formatted as dollars only when printing. No tax rules live in this module.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _to_cents(dollars):
    """Convert a float/str/Decimal dollar amount to int cents (half up)."""
    value = (Decimal(str(dollars)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(value)


def _fmt_money(cents):
    """Format non-negative int cents as '$12.50'."""
    return "$%d.%02d" % (cents // 100, cents % 100)


def _fmt_percent(pct):
    """Format a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    text = "%.2f" % float(pct)
    return text.rstrip("0").rstrip(".")


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_name = customer_id
        region = None
        discount_fraction = 0
    else:
        customer_name = customer["name"]
        region = customer["region"]
        discount_fraction = customer["discount"]

    # pricing-api uses fractions (0.10); tax-api uses percent numbers (10).
    discount_pct = Decimal(str(discount_fraction)) * 100

    output_lines = ["Customer: %s" % customer_name]

    # Collect known lines; keep unknown SKUs in their position.
    priced_lines = []   # for tax: {category, amount_cents}
    subtotal_cents = 0
    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            output_lines.append("UNKNOWN SKU: %s" % sku)
            continue
        unit_cents = _to_cents(item["price"])
        amount_cents = unit_cents * quantity
        subtotal_cents += amount_cents
        priced_lines.append({"category": item["category"], "amount_cents": amount_cents})
        output_lines.append(
            "%s x%d @ %s = %s"
            % (sku, quantity, _fmt_money(unit_cents), _fmt_money(amount_cents))
        )

    # discount = subtotal * percent, rounded to the cent (half up).
    discount_cents = int(
        (Decimal(subtotal_cents) * discount_pct / 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )

    # Tax is computed by tax.py (it applies the discount to taxable lines itself).
    tax_cents = tax.compute_tax_cents(priced_lines, region, float(discount_pct))
    tax_pct = tax.get_tax_pct(region)

    total_cents = subtotal_cents - discount_cents + tax_cents

    output_lines.append("Subtotal: %s" % _fmt_money(subtotal_cents))
    output_lines.append(
        "Discount (%s%%): -%s" % (_fmt_percent(discount_pct), _fmt_money(discount_cents))
    )
    output_lines.append("Tax (%s%%): %s" % (_fmt_percent(tax_pct), _fmt_money(tax_cents)))
    output_lines.append("Total: %s" % _fmt_money(total_cents))

    return "\n".join(output_lines)
