"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed API (pricing_api v2, money_units v1):
    get_item(sku)                -> dict {"sku", "name", "price_cents", "category"} or None
    get_customer(customer_id)    -> dict {"id", "name", "discount_pct", "region"} or None

Units: money is an integer number of cents (1250 = $12.50).
       Percentages are percent numbers (10 = 10%).
A lookup miss returns None (no default value, no KeyError).
This module computes no totals, discounts, or tax.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")


def _parse_percent(text):
    """Parse a percent number: int when it is whole (10 -> 10), otherwise float (8.25 -> 8.25)."""
    value = float(text)
    return int(value) if value.is_integer() else value


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
                "discount_pct": _parse_percent(row["discount_pct"]),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog(os.path.join(_DATA_DIR, "catalog.csv"))
_CUSTOMERS = _load_customers(os.path.join(_DATA_DIR, "customers.csv"))


def get_item(sku):
    """Return a copy of the item record for sku, or None if sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for customer_id, or None if the id is unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
