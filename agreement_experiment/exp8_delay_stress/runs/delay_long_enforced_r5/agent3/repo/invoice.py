"""Invoice module. Owned by agent3. Implements render_invoice(order).

Uses only committed team APIs:
  pricing.get_item(sku) -> Item | None        (Item.price_cents: int, Item.category: str)
  pricing.get_customer(cid) -> Customer | None (Customer.name, .discount_pct: percent number, .region)
  tax.compute_tax(region, discount_pct, lines) -> int cents
      lines = [{"category": str, "amount_cents": int}, ...]; region None -> tax 0
  tax.rate_for_region(region) -> percent number

Money is integer cents at the tax boundary; Decimal is used only for the discount rounding.
"""
from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _money(cents):
    """Format integer cents as $12.50 or -$3.91."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "{}${}.{:02d}".format(sign, cents // 100, cents % 100)


def _percent(value):
    """Format a percent number without trailing zeros: 10, 8.25, 0."""
    text = format(Decimal(str(value)).normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text if text else "0"


def render_invoice(order):
    customer_id = order.get("customer", "")
    customer = pricing.get_customer(customer_id)

    if customer is not None:
        customer_label = customer.name
        region = customer.region
        discount_pct = customer.discount_pct
    else:
        # Unknown customer: shown by id, 0% discount, 0% tax (committed tax.unknown_customer).
        customer_label = customer_id
        region = None
        discount_pct = 0

    out = ["Customer: {}".format(customer_label)]

    tax_lines = []  # {"category", "amount_cents"} for known items only
    subtotal_cents = 0
    for sku, qty in order.get("lines", []):
        item = pricing.get_item(sku)
        if item is None:
            out.append("UNKNOWN SKU: {}".format(sku))
            continue
        line_cents = item.price_cents * qty
        tax_lines.append({"category": item.category, "amount_cents": line_cents})
        subtotal_cents += line_cents
        out.append("{} x{} @ {} = {}".format(
            sku, qty, _money(item.price_cents), _money(line_cents)))

    discount_cents = int(
        (Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100))
        .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    tax_cents = tax.compute_tax(region, discount_pct, tax_lines)
    tax_pct = tax.rate_for_region(region) if region is not None else 0

    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: {}".format(_money(subtotal_cents)))
    out.append("Discount ({}%): -{}".format(_percent(discount_pct), _money(discount_cents)))
    out.append("Tax ({}%): {}".format(_percent(tax_pct), _money(tax_cents)))
    out.append("Total: {}".format(_money(total_cents)))
    return "\n".join(out)
