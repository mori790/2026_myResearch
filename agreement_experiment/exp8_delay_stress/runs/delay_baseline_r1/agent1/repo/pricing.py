"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (as agreed):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)              -> dict {"sku", "name", "price", "category"} or None
  get_item_price(sku)        -> float (dollars) or None
  list_items()               -> list of item dicts, in catalog order
  get_customer(customer_id)  -> dict {"id", "name", "discount", "region"} or None
  get_discount(customer_id)  -> float (fraction, e.g. 0.10) or None
  list_customers()           -> list of customer dicts, in file order

Returned dicts are copies; mutating them does not affect the cached data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path=_CATALOG_PATH):
    """Read catalog.csv. price_cents (integer cents) is converted to dollars."""
    items = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items.append({
                "sku": sku,
                "name": row["name"].strip(),
                "price": int(row["price_cents"]) / 100.0,
                "category": row["category"].strip(),
            })
    return items


def _load_customers(path=_CUSTOMERS_PATH):
    """Read customers.csv. discount_pct (integer percent) is converted to a fraction."""
    customers = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            customers.append({
                "id": row["id"].strip(),
                "name": row["name"].strip(),
                "discount": float(row["discount_pct"]) / 100.0,
                "region": row["region"].strip(),
            })
    return customers


_ITEMS = _load_catalog()
_ITEMS_BY_SKU = {item["sku"]: item for item in _ITEMS}

_CUSTOMERS = _load_customers()
_CUSTOMERS_BY_ID = {c["id"]: c for c in _CUSTOMERS}


def get_item(sku):
    """Return the item with the given SKU as a dict, or None if it does not exist."""
    item = _ITEMS_BY_SKU.get(sku)
    return dict(item) if item is not None else None


def get_item_price(sku):
    """Return the unit price of the item in dollars, or None if the SKU does not exist."""
    item = _ITEMS_BY_SKU.get(sku)
    return item["price"] if item is not None else None


def list_items():
    """Return all catalog items (copies), in catalog order."""
    return [dict(item) for item in _ITEMS]


def get_customer(customer_id):
    """Return the customer with the given id as a dict, or None if it does not exist."""
    customer = _CUSTOMERS_BY_ID.get(customer_id)
    return dict(customer) if customer is not None else None


def get_discount(customer_id):
    """Return the customer's discount as a fraction (0.10 = 10%), or None if the customer does not exist."""
    customer = _CUSTOMERS_BY_ID.get(customer_id)
    return customer["discount"] if customer is not None else None


def list_customers():
    """Return all customers (copies), in file order."""
    return [dict(c) for c in _CUSTOMERS]
