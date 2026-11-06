"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Agreed representation (committed decisions units_repr and pricing_api_v2):
  * Money is an integer number of cents (1250 means $12.50).
  * Percentages are numbers in percent units (10 means 10%).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)                -> dict {sku, name, price_cents, category} or None
  get_customer(customer_id)    -> dict {id, name, discount_pct, region} or None
  list_items()                 -> list of item dicts, in catalog order
  list_customers()             -> list of customer dicts, in file order

Every call returns a fresh copy, so callers cannot change the loaded data.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_FILE = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_FILE = os.path.join(_DATA_DIR, "customers.csv")


def _parse_number(text, field, source):
    """Parse an integer if possible, otherwise a float. Raises ValueError on bad input."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"{source}: field {field!r} is not a number: {text!r}") from None


def _load_items(path):
    items = []  # catalog order
    by_sku = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in by_sku:
                raise ValueError(f"{path}: duplicate sku {sku!r}")
            item = {
                "sku": sku,
                "name": row["name"].strip(),
                "price_cents": int(_parse_number(row["price_cents"], "price_cents", path)),
                "category": row["category"].strip(),
            }
            by_sku[sku] = item
            items.append(item)
    return items, by_sku


def _load_customers(path):
    customers = []  # file order
    by_id = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in by_id:
                raise ValueError(f"{path}: duplicate customer id {cid!r}")
            customer = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": _parse_number(row["discount_pct"], "discount_pct", path),
                "region": row["region"].strip(),
            }
            by_id[cid] = customer
            customers.append(customer)
    return customers, by_id


_ITEMS, _ITEMS_BY_SKU = _load_items(_CATALOG_FILE)
_CUSTOMERS, _CUSTOMERS_BY_ID = _load_customers(_CUSTOMERS_FILE)


def get_item(sku):
    """Return a copy of the item with this SKU, or None if there is no such item."""
    item = _ITEMS_BY_SKU.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer with this id, or None if there is no such customer."""
    customer = _CUSTOMERS_BY_ID.get(customer_id)
    return dict(customer) if customer is not None else None


def list_items():
    """Return copies of all items, in catalog order."""
    return [dict(item) for item in _ITEMS]


def list_customers():
    """Return copies of all customers, in file order."""
    return [dict(customer) for customer in _CUSTOMERS]
