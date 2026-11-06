"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
- Money amounts are floats in dollars (12.5 means $12.50).
- Percentages are fractions (10% is 0.10).
- A lookup that finds nothing returns None.

Public API:
- get_item(sku)            -> dict or None
    {"sku": str, "name": str, "unit_price": float (dollars), "category": str}
- get_customer(customer_id) -> dict or None
    {"id": str, "name": str, "discount": float (fraction, e.g. 0.10), "region": str}
- list_items()             -> list of item dicts (in catalog order)
- list_customers()         -> list of customer dicts (in file order)

Returned dicts are fresh copies; mutating them does not affect the cached data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path):
    items = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            items.append({
                "sku": row["sku"],
                "name": row["name"],
                # Source file stores integer cents; convert to float dollars.
                "unit_price": round(int(row["price_cents"]) / 100, 2),
                "category": row["category"],
            })
    return items


def _load_customers(path):
    customers = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            customers.append({
                "id": row["id"],
                "name": row["name"],
                # Source file stores percentages (10 means 10%); convert to fraction.
                "discount": float(row["discount_pct"]) / 100,
                "region": row["region"],
            })
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_ITEMS_BY_SKU = {item["sku"]: item for item in _ITEMS}

_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)
_CUSTOMERS_BY_ID = {c["id"]: c for c in _CUSTOMERS}


def get_item(sku):
    """Return the item with the given SKU, or None if it does not exist."""
    item = _ITEMS_BY_SKU.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer with the given ID, or None if it does not exist."""
    customer = _CUSTOMERS_BY_ID.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all catalog items as a list of dicts (catalog order)."""
    return [dict(item) for item in _ITEMS]


def list_customers():
    """Return all customers as a list of dicts (file order)."""
    return [dict(c) for c in _CUSTOMERS]
