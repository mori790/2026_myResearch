"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Interface (committed decision pricing_api v2):
  get_item(sku: str) -> dict
      {"sku": str, "name": str, "price_cents": int, "category": str}
      Raises KeyError if the sku is unknown.
  get_customer(customer_id: str) -> dict
      {"id": str, "name": str, "discount_pct": float, "region": str | None}
      discount_pct is a percent number (10 = 10%). region None = no region on file.
      Raises KeyError if the customer id is unknown.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
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
            cid = row["id"].strip()
            region = row["region"].strip() if row.get("region") else ""
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": float(row["discount_pct"].strip()),
                "region": region or None,
            }
    return customers


_ITEMS = _load_items(os.path.join(_DATA_DIR, "catalog.csv"))
_CUSTOMERS = _load_customers(os.path.join(_DATA_DIR, "customers.csv"))


def get_item(sku: str) -> dict:
    """Return a copy of the item record for sku. Raises KeyError if unknown."""
    if sku not in _ITEMS:
        raise KeyError(f"unknown sku: {sku!r}")
    return dict(_ITEMS[sku])


def get_customer(customer_id: str) -> dict:
    """Return a copy of the customer record for customer_id. Raises KeyError if unknown."""
    if customer_id not in _CUSTOMERS:
        raise KeyError(f"unknown customer id: {customer_id!r}")
    return dict(_CUSTOMERS[customer_id])
