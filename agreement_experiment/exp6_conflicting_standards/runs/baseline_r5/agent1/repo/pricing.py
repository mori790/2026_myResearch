"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (followed here):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)            -> Item or None
  get_customer(customer_id)-> Customer or None
  list_items()             -> list[Item]     (catalog order)
  list_customers()         -> list[Customer] (file order)

The raw files store prices in integer cents (price_cents) and discounts as whole
percentages (discount_pct, e.g. 10 means 10%). Both are converted to the team
conventions when the files are loaded; no other module needs to know about the raw format.
"""

import csv
import os
from dataclasses import dataclass

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price: float      # dollars, e.g. 12.5 means $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float   # fraction, e.g. 0.10 means 10% off
    region: str


def _read_rows(path):
    # utf-8-sig tolerates a BOM if the file was saved by a spreadsheet tool.
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def _load_items(path):
    items = {}
    order = []
    for row in _read_rows(path):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"{path}: duplicate sku {sku!r}")
        cents = int(row["price_cents"])  # raises ValueError on malformed data
        if cents < 0:
            raise ValueError(f"{path}: negative price for sku {sku!r}")
        item = Item(
            sku=sku,
            name=row["name"],
            price=round(cents / 100, 2),
            category=row["category"],
        )
        items[sku] = item
        order.append(item)
    return items, order


def _load_customers(path):
    customers = {}
    order = []
    for row in _read_rows(path):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"{path}: duplicate customer id {cid!r}")
        pct = float(row["discount_pct"])  # raises ValueError on malformed data
        if not 0 <= pct <= 100:
            raise ValueError(f"{path}: discount_pct out of range for customer {cid!r}")
        customer = Customer(
            id=cid,
            name=row["name"],
            discount=round(pct / 100, 6),
            region=row["region"],
        )
        customers[cid] = customer
        order.append(customer)
    return customers, order


_ITEMS, _ITEM_LIST = _load_items(_CATALOG_PATH)
_CUSTOMERS, _CUSTOMER_LIST = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the Item with this SKU, or None if there is no such item."""
    return _ITEMS.get(sku)


def get_customer(customer_id):
    """Return the Customer with this id, or None if there is no such customer."""
    return _CUSTOMERS.get(customer_id)


def list_items():
    """Return all items in catalog order."""
    return list(_ITEM_LIST)


def list_customers():
    """Return all customers in file order."""
    return list(_CUSTOMER_LIST)
