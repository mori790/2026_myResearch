"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file.

Shared conventions (committed in agree.py, see `pricing_api`, `money_representation`,
`percent_representation`, `missing_lookup_return`):
  * Money amounts are integer cents (1250 = $12.50), field name `price_cents`.
  * Percentages are percent numbers (10 = 10 percent), field name `discount_pct`.
  * A lookup that finds nothing returns None. Callers must check for None explicitly.

API:
  get_item(sku)                -> {"sku", "name", "price_cents", "category"} or None
  get_customer(customer_id)    -> {"id", "name", "discount_pct", "region"} or None
  list_items()                 -> list of item dicts, in catalog order
  list_customers()             -> list of customer dicts, in file order
"""

import csv
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"


def _parse_number(text):
    """Parse a CSV numeric cell as int when it is integral, else float."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_items(path):
    items = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            items.append({
                "sku": row["sku"].strip(),
                "name": row["name"].strip(),
                "price_cents": int(row["price_cents"]),
                "category": row["category"].strip(),
            })
    return items


def _load_customers(path):
    customers = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            customers.append({
                "id": row["id"].strip(),
                "name": row["name"].strip(),
                "discount_pct": _parse_number(row["discount_pct"]),
                "region": row["region"].strip(),
            })
    return customers


_ITEMS = _load_items(_DATA_DIR / "catalog.csv")
_CUSTOMERS = _load_customers(_DATA_DIR / "customers.csv")
_ITEMS_BY_SKU = {item["sku"]: item for item in _ITEMS}
_CUSTOMERS_BY_ID = {c["id"]: c for c in _CUSTOMERS}


def get_item(sku):
    """Return a copy of the item record for `sku`, or None if the SKU is unknown."""
    item = _ITEMS_BY_SKU.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS_BY_ID.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return copies of all item records, in catalog order."""
    return [dict(item) for item in _ITEMS]


def list_customers():
    """Return copies of all customer records, in file order."""
    return [dict(c) for c in _CUSTOMERS]
