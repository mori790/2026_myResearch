"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku)                -> dict | None   {"sku", "name", "price", "category"}
  get_customer(customer_id)    -> dict | None   {"id", "name", "discount", "region"}
  get_unit_price(sku, cust_id) -> float | None  list price minus customer discount, rounded to cents
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
            if sku in items:
                raise ValueError(f"duplicate sku in catalog: {sku!r}")
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # price_cents is an integer number of cents; convert to float dollars.
                "price": int(row["price_cents"]) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id: {cid!r}")
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # discount_pct is a percentage (10 means 10%); store as a fraction (0.10).
                "discount": float(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return item info for `sku`, or None if the SKU is unknown.

    The returned "price" is the list price in dollars, before any customer discount.
    """
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for `customer_id`, or None if unknown.

    "discount" is a fraction (0.10 means 10% off); "region" is e.g. "TX".
    """
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def get_unit_price(sku, customer_id):
    """Return the per-unit price in dollars for `sku` after `customer_id`'s discount,
    rounded to cents. Returns None if either the SKU or the customer is unknown.

    Tax is NOT included here.
    """
    item = _ITEMS.get(sku)
    customer = _CUSTOMERS.get(customer_id)
    if item is None or customer is None:
        return None
    return round(item["price"] * (1 - customer["discount"]), 2)
