"""Invoice module. Owned by agent3. Implement render_invoice(order).

Other modules used (agreed APIs):
  pricing.get_item(sku)        -> Item | None      Item: sku, name, price (float dollars), category
  pricing.get_customer(cid)    -> Customer | None  Customer: id, name, discount (fraction, 0.10 = 10%), region
  tax.compute_tax(region, lines, discount_pct) -> int cents
      region: customer's region code, or None for an unknown customer (-> 0 tax)
      lines: list of (amount_cents:int, category:str), pre-discount, known skus only
      discount_pct: percent number (10 = 10%)
  tax.tax_rate(region) -> Decimal percent (e.g. 8.25)

Inside this module money is Decimal dollars and rates are multipliers;
conversion to/from the other modules' units happens at the boundary below.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _cents(amount):
    """Round a Decimal dollar amount to the cent (half up)."""
    return Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount):
    """Format a Decimal dollar amount as '$12.50' or '-$3.91'."""
    amount = _cents(amount)
    if amount < 0:
        return "-$" + format(-amount, "f")
    return "$" + format(amount, "f")


def _percent(pct):
    """Format a Decimal percent without trailing zeros: 8.25, 10, 0."""
    return format(Decimal(pct).normalize(), "f")


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is None:
        name = customer_id
        region = None
        discount_rate = Decimal("0")          # 0.10 for 10% off
    else:
        name = customer.name
        region = customer.region
        discount_rate = Decimal(str(customer.discount))

    out = [f"Customer: {name}"]
    known_lines = []  # (sku, pre-discount line amount in Decimal dollars, category)

    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out.append(f"UNKNOWN SKU: {sku}")
            continue
        unit_price = Decimal(str(item.price))
        amount = _cents(unit_price * qty)
        known_lines.append((amount, item.category))
        out.append(f"{sku} x{qty} @ {_money(unit_price)} = {_money(amount)}")

    subtotal = _cents(sum((amt for amt, _ in known_lines), Decimal("0")))
    discount_pct = discount_rate * HUNDRED
    discount = _cents(subtotal * discount_rate)

    # tax.py owns all tax rules; we only pass it the data it asks for.
    tax_cents = tax.compute_tax(
        region,
        [(int(amt * 100), cat) for amt, cat in known_lines],
        float(discount_pct),
    )
    tax_amount = Decimal(tax_cents) / HUNDRED
    if region is None:
        tax_pct = Decimal("0")
    else:
        tax_pct = Decimal(str(tax.tax_rate(region)))

    total = _cents(subtotal - discount + tax_amount)

    out.append(f"Subtotal: {_money(subtotal)}")
    out.append(f"Discount ({_percent(discount_pct)}%): -{_money(discount)}")
    out.append(f"Tax ({_percent(tax_pct)}%): {_money(tax_amount)}")
    out.append(f"Total: {_money(total)}")
    return "\n".join(out)
