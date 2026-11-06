"""Invoice module. Owned by agent3. Implement render_invoice(order).

All item, customer and tax information comes from pricing.py and tax.py.
Money is handled as integer cents (pricing) and Decimal dollars (tax).
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format a non-negative integer number of cents as $X.YY."""
    return f"${cents // 100}.{cents % 100:02d}"


def _signed_money(cents):
    """Format a non-negative cent amount as -$X.YY (for discounts)."""
    return f"-{_money(cents)}"


def _pct(value):
    """Format a percent without trailing zeros: 10, 8.25, 0."""
    d = Decimal(str(value))
    return format(d.normalize(), "f")


def _dollars_to_cents(amount):
    """Convert a Decimal dollar amount to integer cents, rounding half up."""
    cents = (Decimal(amount) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def render_invoice(order):
    customer_id = order["customer"]

    # Resolve the customer. Unknown customers are shown by id with 0% discount and 0% tax.
    try:
        customer = pricing.get_customer(customer_id)
    except pricing.UnknownCustomerError:
        customer = None

    # Resolve each line. Unknown SKUs are reported in place and skipped.
    out_lines = []
    known = []  # (sku, quantity, line_cents, category)
    for sku, qty in order["lines"]:
        try:
            item = pricing.get_item(sku)
        except pricing.UnknownItemError:
            out_lines.append(f"UNKNOWN SKU: {sku}")
            continue
        line_cents = pricing.line_subtotal_cents(sku, qty)
        known.append((sku, qty, line_cents, item))
        out_lines.append(
            f"{sku} x{qty} @ {_money(item.price_cents)} = {_money(line_cents)}"
        )

    subtotal_cents = sum(line_cents for _, _, line_cents, _ in known)

    if customer is None:
        name = customer_id
        discount_pct = Decimal("0")
        discount_c = 0
        tax_pct = Decimal("0")
        tax_c = 0
    else:
        name = customer.name
        discount_pct = customer.discount_pct
        discount_c = pricing.discount_cents(customer_id, subtotal_cents)
        tax_lines = [
            {"amount": Decimal(line_cents) / 100, "category": item.category}
            for _, _, line_cents, item in known
        ]
        tax_amount = tax.compute_tax(tax_lines, customer.region, customer.discount_pct)
        tax_pct = tax.tax_pct_for_region(customer.region)
        tax_c = _dollars_to_cents(tax_amount)

    total_c = subtotal_cents - discount_c + tax_c

    result = [f"Customer: {name}"]
    result.extend(out_lines)
    result.append(f"Subtotal: {_money(subtotal_cents)}")
    result.append(f"Discount ({_pct(discount_pct)}%): {_signed_money(discount_c)}")
    result.append(f"Tax ({_pct(tax_pct)}%): {_money(tax_c)}")
    result.append(f"Total: {_money(total_c)}")
    return "\n".join(result)
