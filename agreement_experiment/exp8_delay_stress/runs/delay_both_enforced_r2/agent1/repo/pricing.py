"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed decisions (agree.py log) that this module follows:
  - money_unit v4:          money is decimal.Decimal in dollars, quantized to 0.01 with ROUND_HALF_UP
                            (catalog price_cents 1250 -> Decimal('12.50')).
  - percent_unit v3:        percentages are plain numbers (10 means 10%, 8.25 means 8.25%).
  - not_found_signal v3:    lookups that find nothing return None. Callers (invoice.py) must check
                            for None and fail loudly; this module never returns a fake default.
  - pricing_api v3:         get_item(sku), get_customer(customer_id), list_items().

Returned dicts are fresh copies, so callers cannot modify the cached data.
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CENT = Decimal("0.01")


def _read_csv(filename):
    """Read a CSV file from data_pricing/ and return a list of dict rows with stripped values."""
    path = os.path.join(_DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {(key or "").strip(): (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(f)
        ]


def _cents_to_dollars(price_cents):
    """Convert an integer cent amount (string or int) to a Decimal dollar amount, e.g. 1250 -> 12.50."""
    return (Decimal(price_cents) / 100).quantize(_CENT, rounding=ROUND_HALF_UP)


def _load_items():
    items = []
    for row in _read_csv("catalog.csv"):
        items.append({
            "sku": row["sku"],
            "name": row["name"],
            "price": _cents_to_dollars(row["price_cents"]),
            "category": row["category"],
        })
    return items


def _load_customers():
    customers = {}
    for row in _read_csv("customers.csv"):
        customers[row["id"]] = {
            "id": row["id"],
            "name": row["name"],
            # Percent number: discount_pct 10 means 10%.
            "discount": Decimal(row["discount_pct"]),
            "region": row["region"],
        }
    return customers


_ITEMS = _load_items()                      # catalog order
_ITEMS_BY_SKU = {item["sku"]: item for item in _ITEMS}
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return the item dict {sku, name, price (Decimal dollars), category} for sku, or None if unknown."""
    item = _ITEMS_BY_SKU.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer dict {id, name, discount (percent number), region}, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all item dicts in catalog order."""
    return [dict(item) for item in _ITEMS]
