"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Implements the committed team decisions:
  - MONEY_UNIT:    money amounts are float dollars (12.5 means $12.50).
  - PERCENT_UNIT:  percentages are fractions (0.10 means 10%).
  - LOOKUP_MISS:   a lookup that finds nothing returns None (never raises).
  - PRICING_API (v2):
      unit_price(sku)              -> float dollars, or None if the sku is unknown
      item_name(sku)               -> str or None
      item_category(sku)           -> str or None
      customer(customer_id)        -> dict {"name": str, "region": str, "discount": float fraction}
                                      or None if the customer is unknown

The data files are in data_pricing/ next to this module and are loaded relative to this file.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path):
    """Read catalog.csv (sku,name,price_cents,category) into {sku: item dict}."""
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate sku in {path}: {sku!r}")
            items[sku] = {
                "name": row["name"].strip(),
                # MONEY_UNIT: the file stores integer cents; convert to float dollars.
                "price": int(row["price_cents"]) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    """Read customers.csv (id,name,discount_pct,region) into {id: customer dict}."""
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id in {path}: {cid!r}")
            customers[cid] = {
                "name": row["name"].strip(),
                "region": row["region"].strip(),
                # PERCENT_UNIT: the file stores a percent number (10 means 10%); convert to a fraction.
                "discount": float(row["discount_pct"]) / 100,
            }
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def unit_price(sku):
    """Return the unit price of `sku` in float dollars, or None if the sku is unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item["price"]


def item_name(sku):
    """Return the item name for `sku`, or None if the sku is unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item["name"]


def item_category(sku):
    """Return the item category for `sku`, or None if the sku is unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item["category"]


def customer(customer_id):
    """Return {"name", "region", "discount"} for the customer, or None if unknown.

    "discount" is a float fraction (0.10 means 10% off). A fresh dict is returned each time,
    so callers cannot change the module's internal data by mutating it.
    """
    c = _CUSTOMERS.get(customer_id)
    return None if c is None else dict(c)
