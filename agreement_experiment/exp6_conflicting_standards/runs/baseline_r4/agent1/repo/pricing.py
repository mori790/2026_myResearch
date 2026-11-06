"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (followed here):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)      -> item dict or None
                        keys: sku (str), name (str), price (float, dollars), category (str)
  get_customer(cid)  -> customer dict or None
                        keys: id (str), name (str), discount (float fraction, 0.10 = 10% off),
                              region (str)
  all_items()        -> list of item dicts (catalog order)
  all_customers()    -> list of customer dicts (file order)

The returned dicts are fresh copies; mutating them does not affect the module's data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_FILE = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_FILE = os.path.join(_DATA_DIR, "customers.csv")


def _read_rows(path):
    """Read a CSV file into a list of dicts with stripped keys and values; skips blank lines."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
            if not any(row.values()):
                continue
            rows.append(row)
    return rows


def _load_items():
    items = {}
    for row in _read_rows(_CATALOG_FILE):
        sku = row["sku"]
        if sku in items:
            raise ValueError("duplicate sku in catalog.csv: %r" % sku)
        items[sku] = {
            "sku": sku,
            "name": row["name"],
            # Source stores integer cents; convert to float dollars.
            "price": round(int(row["price_cents"]) / 100, 2),
            "category": row["category"],
        }
    return items


def _load_customers():
    customers = {}
    for row in _read_rows(_CUSTOMERS_FILE):
        cid = row["id"]
        if cid in customers:
            raise ValueError("duplicate id in customers.csv: %r" % cid)
        customers[cid] = {
            "id": cid,
            "name": row["name"],
            # Source stores whole percentages; convert to a fraction.
            "discount": round(int(row["discount_pct"]) / 100, 4),
            "region": row["region"],
        }
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return item info for `sku` as a dict, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return customer info for `customer_id` as a dict, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def all_items():
    """Return all catalog items (catalog order) as a list of dicts."""
    return [dict(item) for item in _ITEMS.values()]


def all_customers():
    """Return all customers (file order) as a list of dicts."""
    return [dict(c) for c in _CUSTOMERS.values()]
