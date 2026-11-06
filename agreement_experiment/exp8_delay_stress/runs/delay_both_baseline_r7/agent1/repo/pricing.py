"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Public API (team convention: money in float dollars, percentages as fractions, misses return None):

    get_item(sku: str) -> Item | None
    get_customer(customer_id: str) -> Customer | None
    all_items() -> list[Item]
    all_customers() -> list[Customer]

Item fields:     sku (str), name (str), price (float, dollars), category (str)
Customer fields: id (str), name (str), discount (float, fraction e.g. 0.10), region (str)

Customer.region is passed through unchanged; this module does not interpret it (tax is tax.py's job).
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
    discount: float   # fraction, e.g. 0.10 means 10%
    region: str


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            # CSV stores price in integer cents; convert to float dollars.
            price = round(int(row["price_cents"]) / 100, 2)
            items[sku] = Item(sku=sku, name=row["name"].strip(), price=price,
                              category=row["category"].strip())
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            # CSV stores discount as a percentage (10 means 10%); convert to fraction.
            discount = round(float(row["discount_pct"]) / 100, 6)
            customers[cid] = Customer(id=cid, name=row["name"].strip(), discount=discount,
                                      region=row["region"].strip())
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the Item for sku, or None if there is no such item."""
    return _ITEMS.get(sku)


def get_customer(customer_id):
    """Return the Customer for customer_id, or None if there is no such customer."""
    return _CUSTOMERS.get(customer_id)


def all_items():
    """Return all items in catalog order."""
    return list(_ITEMS.values())


def all_customers():
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())
