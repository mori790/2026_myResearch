"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Shared conventions (committed in the team decision log):
  - Money: floats in dollars (12.5 means $12.50). Never cents.
  - Percentages: fractions (10% is 0.10).
  - A lookup with no match returns None.
  - Customer region: two-letter state code string, verbatim from customers.csv.

Public API:
  get_item(sku: str) -> dict | None
      keys: sku, name, unit_price (float dollars), category
  get_customer(customer_id: str) -> dict | None
      keys: id, name, discount (fraction), region (str)
  list_skus() -> list[str]   (catalog order)
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path=_CATALOG_PATH):
    """Return an ordered dict sku -> item record, read from catalog.csv."""
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # catalog stores integer cents; convert to float dollars
                "unit_price": int(row["price_cents"].strip()) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path=_CUSTOMERS_PATH):
    """Return a dict customer_id -> customer record, read from customers.csv."""
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # customers.csv stores percent points; convert to a fraction
                "discount": float(row["discount_pct"].strip()) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return a copy of the item record for sku, or None if sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for customer_id, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def list_skus():
    """Return all SKUs in catalog order."""
    return list(_ITEMS.keys())
