"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Agreed interface (decision log: PRICING_API v2, committed):
    get_item(sku: str) -> dict | None
        keys: sku (str), name (str), price_cents (int, 1250 = $12.50), category (str)
    get_customer(customer_id: str) -> dict | None
        keys: id (str), name (str), discount (float fraction, 0.10 = 10%, 0.0 if none),
              region (str, uppercase US state code such as "TX")

Both functions return None when nothing is found. Money is int cents and
percentages are fractions, following the project-wide convention.

The data files are in data_pricing/ next to this file.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price_cents": int(row["price_cents"]),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # The CSV stores percent numbers (10 means 10%); the interface uses fractions.
                "discount": int(row["discount_pct"]) / 100.0,
                "region": row["region"].strip().upper(),
            }
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return item info for sku as a new dict, or None if the sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for customer_id as a new dict, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
