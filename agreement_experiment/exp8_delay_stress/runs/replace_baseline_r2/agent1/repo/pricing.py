"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (followed here):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)          -> dict {"sku", "name", "price", "category"} or None
                            price: float, dollars
  get_customer(cust_id)  -> dict {"id", "name", "discount", "region"} or None
                            discount: float fraction (0.10 means 10% off)
  list_items()           -> list of item dicts, in catalog order
  list_customers()       -> list of customer dicts, in file order

Returned dicts are copies; mutating them does not affect the cached data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Source file stores integer cents; convert to float dollars.
                "price": int(row["price_cents"].strip()) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cust_id = row["id"].strip()
            customers[cust_id] = {
                "id": cust_id,
                "name": row["name"].strip(),
                # Source file stores whole percent; convert to a fraction.
                "discount": int(row["discount_pct"].strip()) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the item with the given SKU as a dict, or None if it does not exist."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(cust_id):
    """Return the customer with the given ID as a dict, or None if it does not exist."""
    customer = _CUSTOMERS.get(cust_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return all catalog items as a list of dicts, in catalog order."""
    return [dict(item) for item in _ITEMS.values()]


def list_customers():
    """Return all customers as a list of dicts, in file order."""
    return [dict(customer) for customer in _CUSTOMERS.values()]
