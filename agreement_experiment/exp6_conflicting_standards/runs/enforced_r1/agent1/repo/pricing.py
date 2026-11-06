"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

API (agreed in the decision log as topic 'pricing_api'):
    get_item(sku: str) -> dict | None
        {"sku": str, "name": str, "price": float, "category": str}
        price is in dollars (12.5 means $12.50). None if the SKU is unknown.
    get_customer(customer_id: str) -> dict | None
        {"id": str, "name": str, "discount": float, "region": str}
        discount is a fraction (0.10 means 10%). None if the customer is unknown.
    list_skus() -> list[str]
        All SKUs in catalog order.

Team standard: money is a float in dollars, percentages are fractions,
and a lookup that finds nothing returns None.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path):
    """Read catalog.csv. Returns an ordered dict: sku -> item dict."""
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # The data stores prices in integer cents; convert to float dollars.
                "price": int(row["price_cents"]) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    """Read customers.csv. Returns a dict: customer id -> customer dict."""
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # The data stores percentages as numbers (10 means 10%); convert to a fraction.
                "discount": float(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return item info for sku as a new dict, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for customer_id as a new dict, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_skus():
    """Return all SKUs in catalog order."""
    return list(_ITEMS.keys())
