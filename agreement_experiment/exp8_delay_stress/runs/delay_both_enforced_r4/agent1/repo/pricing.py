"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Public API (committed decision: pricing_api v2):
- get_item(sku) -> {"sku": str, "name": str, "unit_price_cents": int, "category": str} or None
    unit_price_cents: integer cents (1250 means $12.50)
- get_customer(customer_id) -> {"id": str, "name": str, "discount_pct": number, "region": str or None} or None
    discount_pct: percent number (10 means 10%)
    region: e.g. "TX"; None if the customer has no region

Lookups that find nothing return None. Callers get fresh dicts, so mutating
a returned value does not affect the module's data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _parse_number(text):
    """Parse a CSV number: integer if it is written as one, otherwise float."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "unit_price_cents": int(row["price_cents"].strip()),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            region = row["region"].strip() or None
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": _parse_number(row["discount_pct"]),
                "region": region,
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return item info for `sku`, or None if the SKU is unknown."""
    if not isinstance(sku, str):
        return None
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for `customer_id`, or None if the ID is unknown."""
    if not isinstance(customer_id, str):
        return None
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
