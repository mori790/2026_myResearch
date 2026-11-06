"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Agreed API (committed decision `pricing_api` v3):
- get_item(sku) -> dict with keys: sku, name, unit_price_cents (int), category
- get_customer(customer_id) -> dict with keys: id, name, discount_pct (int, 10 = 10%), region
- Money is integer cents (1250 = $12.50). Percentages are percent numbers (10 = 10%).
- Unknown sku or customer id raises KeyError.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items():
    items = {}
    with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "unit_price_cents": int(row["price_cents"]),
                "category": row["category"].strip(),
            }
    return items


def _load_customers():
    customers = {}
    with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": int(row["discount_pct"]),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return item info for `sku`. Raises KeyError if the sku is unknown."""
    return dict(_ITEMS[sku])


def get_customer(customer_id):
    """Return customer info for `customer_id`. Raises KeyError if the id is unknown."""
    return dict(_CUSTOMERS[customer_id])
