"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (followed everywhere in this module):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API (committed decision `pricing_api` v1):
  get_item(sku)             -> Item or None
  get_price(sku)            -> float (dollars) or None
  list_items()              -> list[Item]     (catalog order)
  get_customer(customer_id) -> Customer or None
  get_discount(customer_id) -> float (fraction, e.g. 0.10) or None
  get_region(customer_id)   -> str (e.g. "TX") or None
  list_customers()          -> list[Customer] (file order)

The data files store prices in integer cents (price_cents) and discounts as
whole percents (discount_pct); this module converts them to the team convention.
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
    customer_id: str
    name: str
    discount: float   # fraction, e.g. 0.10 means 10% off
    region: str       # e.g. "TX", "OR", "NY"


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate SKU in {path}: {sku!r}")
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                price=int(row["price_cents"]) / 100.0,
                category=row["category"].strip(),
            )
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id in {path}: {cid!r}")
            customers[cid] = Customer(
                customer_id=cid,
                name=row["name"].strip(),
                discount=float(row["discount_pct"]) / 100.0,
                region=row["region"].strip(),
            )
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the Item for `sku`, or None if the SKU is not in the catalog."""
    return _ITEMS.get(sku)


def get_price(sku):
    """Return the unit price in dollars for `sku`, or None if unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else item.price


def list_items():
    """Return all catalog items in catalog order."""
    return list(_ITEMS.values())


def get_customer(customer_id):
    """Return the Customer for `customer_id`, or None if unknown."""
    return _CUSTOMERS.get(customer_id)


def get_discount(customer_id):
    """Return the customer's discount as a fraction (0.10 = 10%), or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return None if customer is None else customer.discount


def get_region(customer_id):
    """Return the customer's region code (e.g. "TX"), or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return None if customer is None else customer.region


def list_customers():
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())
