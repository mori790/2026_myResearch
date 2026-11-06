"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed API (decision topic: pricing_api v1):
  get_item(sku: str) -> dict | None
      {"sku": str, "name": str, "unit_price": float (dollars), "category": str}
  get_customer(customer_id: str) -> dict | None
      {"id": str, "name": str, "discount_rate": float (fraction, 0.10 = 10%), "region": str}
Lookups that find nothing return None. Money is float dollars; percents are fractions.
This module does not compute tax or apply discounts."""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")


def _load_catalog():
    items = {}
    with open(os.path.join(_DATA_DIR, "catalog.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # CSV stores integer cents; convert to float dollars.
                "unit_price": int(row["price_cents"]) / 100,
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
                # CSV stores a percent number (10 = 10%); convert to a fraction.
                "discount_rate": int(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return item info for sku as a dict, or None if the sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for customer_id as a dict, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
