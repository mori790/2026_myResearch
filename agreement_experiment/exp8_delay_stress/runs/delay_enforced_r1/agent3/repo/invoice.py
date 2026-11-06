"""Invoice module. Owned by agent3. Implement render_invoice(order).

Interfaces used (committed in the shared decision log):

  pricing.get_item(sku)      -> Item(sku, name, price_cents, category)
                                raises KeyError if the sku is unknown
  pricing.get_customer(cid)  -> Customer(id, name, discount_pct, region)
                                raises KeyError if the customer is unknown
  tax.compute_tax(region, discount_pct, lines) -> int cents
                                lines = [(category, amount_cents), ...]
                                region None -> 0
  tax.tax_pct(region)        -> percent number (8.25 = 8.25%), None -> 0

Money is int cents at the module boundary (committed money.representation).
Inside this module, cents are shown as Decimal dollars (team standard).
This module does not compute tax rules; it only passes data to tax.py.
"""

from decimal import Decimal, ROUND_HALF_UP

import pricing
import tax


def _find(lookup, key):
    """Return the record for key, or None if the lookup raises KeyError."""
    try:
        return lookup(key)
    except KeyError:
        return None


def _pct_text(percent):
    """Show a percent number without trailing zeros: 10 -> '10', 8.25 -> '8.25', 0 -> '0'."""
    return format(Decimal(str(percent)).normalize(), "f")


def _money(cents):
    """Format int cents as a dollar string, e.g. 1250 -> '$12.50'."""
    return "$" + format(Decimal(cents) / Decimal(100), ".2f")


def _round_cents(value):
    """Round a Decimal amount in cents to a whole cent, half up."""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def render_invoice(order):
    customer_id = order["customer"]
    customer = _find(pricing.get_customer, customer_id)
    if customer is not None:
        customer_name = customer.name
        discount_pct = customer.discount_pct
        region = customer.region
    else:
        # Unknown customer: shown by id, 0% discount, 0% tax.
        customer_name = customer_id
        discount_pct = 0
        region = None

    out = ["Customer: " + customer_name]
    subtotal_cents = 0
    taxable_lines = []  # (category, amount_cents) for every known line

    for sku, qty in order["lines"]:
        item = _find(pricing.get_item, sku)
        if item is None:
            out.append("UNKNOWN SKU: " + sku)
            continue
        amount_cents = item.price_cents * qty
        subtotal_cents += amount_cents
        taxable_lines.append((item.category, amount_cents))
        out.append(
            "{} x{} @ {} = {}".format(
                sku, qty, _money(item.price_cents), _money(amount_cents)
            )
        )

    discount_cents = _round_cents(
        Decimal(subtotal_cents) * Decimal(str(discount_pct)) / Decimal(100)
    )
    tax_cents = tax.compute_tax(region, discount_pct, taxable_lines)
    tax_pct = tax.tax_pct(region)
    total_cents = subtotal_cents - discount_cents + tax_cents

    out.append("Subtotal: " + _money(subtotal_cents))
    out.append(
        "Discount ({}%): -{}".format(_pct_text(discount_pct), _money(discount_cents))
    )
    out.append("Tax ({}%): {}".format(_pct_text(tax_pct), _money(tax_cents)))
    out.append("Total: " + _money(total_cents))

    return "\n".join(out)
