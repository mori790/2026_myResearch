"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Shared API (committed decision: module_api v3):
    get_item(sku)                -> dict | None
        {"sku": str, "name": str, "unit_price_cents": int, "category": str}
    get_customer(customer_id)    -> dict | None
        {"id": str, "name": str, "discount_pct": number, "region": str}

Units: money is integer cents; percentages are percent numbers (10 means 10%).
A lookup that finds nothing returns None.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")


def _parse_number(text):
    """Parse a percent value from the data file: int if possible, otherwise float."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_items():
    items = {}
    with open(os.path.join(_DATA_DIR, "catalog.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "unit_price_cents": int(row["price_cents"].strip()),
                "category": row["category"].strip(),
            }
    return items


def _load_customers():
    customers = {}
    with open(os.path.join(_DATA_DIR, "customers.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": _parse_number(row["discount_pct"]),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return item information for a SKU, or None if the SKU is unknown.

    Returns a copy, so callers cannot modify the loaded data.
    """
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer information for an ID, or None if the ID is unknown.

    Returns a copy, so callers cannot modify the loaded data.
    """
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
