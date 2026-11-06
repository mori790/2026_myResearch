"""Invoice module. Owned by agent3.

render_invoice(order) builds the text of an invoice. It gets item, customer
and tax information from pricing.py and tax.py and does not apply tax rules.

Agreed API (pricing_api and tax_api in shared/agreement_log.jsonl):
  pricing.get_item(sku)                 -> dict {sku, name, price (float dollars), category} or None
  pricing.get_customer(customer_id)     -> dict {id, name, discount_pct (fraction, 10 -> 0.10), region} or None
  tax.compute_tax(lines, region, discount_pct=0) -> int cents
      lines: (category, amount_cents) pairs; region None means 0% tax;
      discount_pct is in percent (e.g. 10)
  tax.tax_pct(region)                   -> float percent (None -> 0.0)

Inside this module money is decimal.Decimal dollars.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")


def _money(amount):
    """Format a Decimal dollar amount as '$12.50' (negative: '-$3.91')."""
    amount = amount.quantize(CENT, rounding=ROUND_HALF_UP)
    if amount < 0:
        return "-$" + format(-amount, "f")
    return "$" + format(amount, "f")


def _percent_text(percent):
    """Format a percent without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    value = Decimal(str(percent)).normalize()
    return format(value, "f")


def _to_decimal(value):
    """Convert a float (or int/str) amount to Decimal without float noise."""
    return Decimal(str(value))


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_label = str(customer_id)
        discount_fraction = Decimal("0")
        region = None
    else:
        customer_label = customer.get("name") or str(customer_id)
        discount_fraction = _to_decimal(customer.get("discount_pct", 0))
        region = customer.get("region")

    out_lines = ["Customer: " + customer_label]

    subtotal = Decimal("0")
    tax_lines = []  # (category, amount_cents) pairs for tax.py

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out_lines.append("UNKNOWN SKU: " + str(sku))
            continue

        unit_price = _to_decimal(item["price"])
        quantity = int(quantity)
        line_amount = unit_price * quantity
        subtotal += line_amount

        out_lines.append(
            "{} x{} @ {} = {}".format(
                sku, quantity, _money(unit_price), _money(line_amount)
            )
        )

        amount_cents = int(
            (line_amount * 100).to_integral_value(rounding=ROUND_HALF_UP)
        )
        tax_lines.append((item.get("category", ""), amount_cents))

    discount = (subtotal * discount_fraction).quantize(CENT, rounding=ROUND_HALF_UP)

    # tax.py applies the discount to the taxable amount itself; it takes the
    # discount in percent (e.g. 10), so convert the fraction to percent.
    discount_percent = discount_fraction * 100
    tax_cents = tax.compute_tax(tax_lines, region, discount_pct=float(discount_percent))
    tax_amount = (Decimal(tax_cents) / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    tax_percent = Decimal(str(tax.tax_pct(region)))

    total = subtotal - discount + tax_amount

    out_lines.append("Subtotal: " + _money(subtotal))
    out_lines.append(
        "Discount ({}%): -{}".format(_percent_text(discount_percent), _money(discount))
    )
    out_lines.append(
        "Tax ({}%): {}".format(_percent_text(tax_percent), _money(tax_amount))
    )
    out_lines.append("Total: " + _money(total))

    return "\n".join(out_lines)
