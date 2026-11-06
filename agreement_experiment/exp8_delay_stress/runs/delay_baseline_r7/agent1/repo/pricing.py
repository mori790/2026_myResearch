"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (followed here):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku)          -> Item or None
  get_customer(cust_id)  -> Customer or None
  get_price(sku)         -> float (dollars) or None
  get_discount(cust_id)  -> float (fraction, e.g. 0.10) or None
  all_items()            -> list[Item]
  all_customers()        -> list[Customer]
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
    price: float      # dollars, e.g. 12.5 == $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float   # fraction, e.g. 0.10 == 10% off
    region: str


def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in reader]


def _load_items(path):
    items = {}
    for row in _read_rows(path):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate sku in catalog: {sku!r}")
        items[sku] = Item(
            sku=sku,
            name=row["name"],
            price=int(row["price_cents"]) / 100.0,   # cents -> dollars
            category=row["category"],
        )
    return items


def _load_customers(path):
    customers = {}
    for row in _read_rows(path):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate customer id: {cid!r}")
        customers[cid] = Customer(
            id=cid,
            name=row["name"],
            discount=int(row["discount_pct"]) / 100.0,  # percent -> fraction
            region=row["region"],
        )
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the Item for `sku`, or None if it is not in the catalog."""
    return _ITEMS.get(sku)


def get_customer(cust_id):
    """Return the Customer for `cust_id`, or None if unknown."""
    return _CUSTOMERS.get(cust_id)


def get_price(sku):
    """Unit price in dollars for `sku`, or None if unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item.price


def get_discount(cust_id):
    """Discount fraction (0.10 == 10%) for `cust_id`, or None if unknown."""
    customer = _CUSTOMERS.get(cust_id)
    return None if customer is None else customer.discount


def all_items():
    """All catalog items, in catalog order."""
    return list(_ITEMS.values())


def all_customers():
    """All customers, in file order."""
    return list(_CUSTOMERS.values())
