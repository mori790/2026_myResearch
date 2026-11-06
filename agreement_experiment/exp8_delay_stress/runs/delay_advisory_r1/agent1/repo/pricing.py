"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed API (decision log topic: pricing_api v2):

    get_item(sku: str) -> dict | None
        {"sku": str, "name": str, "price_cents": int, "category": str}
        price_cents is an integer number of cents (1250 means $12.50).
        Returns None if the sku is unknown.

    get_customer(customer_id: str) -> dict | None
        {"id": str, "name": str, "discount_pct": number, "region": str}
        discount_pct is a percent number (10 means 10%).
        Returns None if the customer is unknown.

Ids and skus are case-sensitive strings. This module supplies data only;
it does not compute tax or totals.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _parse_number(text):
    """Parse a CSV number: integers stay int, decimals become float."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def _load_catalog(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate sku in {path}: {sku!r}")
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price_cents": int(row["price_cents"].strip()),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            customer_id = row["id"].strip()
            if customer_id in customers:
                raise ValueError(f"duplicate customer id in {path}: {customer_id!r}")
            customers[customer_id] = {
                "id": customer_id,
                "name": row["name"].strip(),
                "discount_pct": _parse_number(row["discount_pct"]),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return a copy of the item record for `sku`, or None if the sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
