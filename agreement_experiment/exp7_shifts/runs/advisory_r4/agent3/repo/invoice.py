"""Invoice module. Owned by agent3. Implement render_invoice(order).

Uses only the committed APIs:
  pricing.get_item(sku) / pricing.get_customer(customer_id)   (agent1, tax/pricing.api v1)
  tax.compute_tax(customer, lines)                            (agent2, tax.api v1)

Conventions (committed): money = float dollars, percent = fraction, lookup miss = None.
Rounding is done with Decimal (ROUND_HALF_UP, cent) to avoid float drift.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")

# Synthetic category used only to read the tax rate back out of tax.compute_tax.
# tax.api v1 says only exempt categories are skipped, so this category is taxable.
_RATE_PROBE_CATEGORY = "__rate_probe__"
_RATE_PROBE_AMOUNT = 100000000.0  # 1e8 dollars: cent rounding error is ~1e-10 of the rate


def _money(value):
    """Convert a float dollar amount to a Decimal rounded half-up to the cent."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _percent_text(fraction):
    """Format a fraction as a percent string without trailing zeros (0.0825 -> '8.25')."""
    pct = (Decimal(str(fraction)) * 100).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    text = format(pct.normalize(), "f")
    return text


def _tax_rate(customer):
    """Return the tax rate (fraction) that tax.py applies to this customer.

    tax.api v1 only exposes compute_tax (amount), not the rate. The rate is read back
    by asking compute_tax for the tax on a large synthetic taxable line with discount 0.
    Unknown customer (None) -> 0% tax, as tax.py defines.
    """
    if customer is None:
        return Decimal("0")
    probe_customer = dict(customer)
    probe_customer["discount"] = 0.0
    probe_tax = _money(tax.compute_tax(probe_customer, [
        {"category": _RATE_PROBE_CATEGORY, "amount": _RATE_PROBE_AMOUNT},
    ]))
    return probe_tax / Decimal(str(_RATE_PROBE_AMOUNT))


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        customer_label = customer_id
        discount_fraction = Decimal("0")
    else:
        customer_label = customer["name"]
        discount_fraction = Decimal(str(customer["discount"]))

    output = [f"Customer: {customer_label}"]
    tax_lines = []
    subtotal = Decimal("0.00")

    for sku, quantity in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            output.append(f"UNKNOWN SKU: {sku}")
            continue
        line_amount = _money(Decimal(str(item["price"])) * quantity)
        subtotal += line_amount
        output.append(
            f"{sku} x{quantity} @ ${_money(item['price'])} = ${line_amount}"
        )
        tax_lines.append({"category": item["category"], "amount": float(line_amount)})

    discount = _money(subtotal * discount_fraction)
    tax_amount = _money(tax.compute_tax(customer, tax_lines))
    tax_rate = _tax_rate(customer)
    total = subtotal - discount + tax_amount

    output.append(f"Subtotal: ${subtotal}")
    output.append(f"Discount ({_percent_text(discount_fraction)}%): -${discount}")
    output.append(f"Tax ({_percent_text(tax_rate)}%): ${tax_amount}")
    output.append(f"Total: ${total}")

    return "\n".join(output)
