"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file.

Committed interface (see agree.py decisions pricing.money, pricing.percent,
pricing.miss, pricing.api):

    get_item(sku)            -> dict {sku, name, unit_price, category} or None
    get_customer(customer_id)-> dict {id, name, discount, region} or None
    list_items()             -> list of item dicts, in catalog order
    list_customers()         -> list of customer dicts, in file order

Units:
    unit_price : float dollars (12.5 means $12.50)
    discount   : float fraction (0.10 means 10%)

Lookups that find nothing return None. Returned dicts are copies, so
callers cannot change the data held by this module.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path):
    """Read catalog.csv. price_cents (integer cents) is converted to float dollars."""
    items = []
    seen = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in seen:
                raise ValueError(f"duplicate SKU in catalog.csv: {sku!r}")
            seen.add(sku)
            items.append({
                "sku": sku,
                "name": row["name"].strip(),
                "unit_price": round(int(row["price_cents"].strip()) / 100, 2),
                "category": row["category"].strip(),
            })
    return items


def _load_customers(path):
    """Read customers.csv. discount_pct (whole percent) is converted to a fraction."""
    customers = []
    seen = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in seen:
                raise ValueError(f"duplicate customer id in customers.csv: {cid!r}")
            seen.add(cid)
            customers.append({
                "id": cid,
                "name": row["name"].strip(),
                "discount": round(float(row["discount_pct"].strip()) / 100, 10),
                "region": row["region"].strip(),
            })
    return customers


# Loaded once when the module is imported.
_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)
_ITEMS_BY_SKU = {item["sku"]: item for item in _ITEMS}
_CUSTOMERS_BY_ID = {cust["id"]: cust for cust in _CUSTOMERS}


def get_item(sku):
    """Return a copy of the item dict for sku, or None if sku is not in the catalog."""
    item = _ITEMS_BY_SKU.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer dict for customer_id, or None if not found."""
    customer = _CUSTOMERS_BY_ID.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return copies of all item dicts, in catalog order."""
    return [dict(item) for item in _ITEMS]


def list_customers():
    """Return copies of all customer dicts, in file order."""
    return [dict(cust) for cust in _CUSTOMERS]
