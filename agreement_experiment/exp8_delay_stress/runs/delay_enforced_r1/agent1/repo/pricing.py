"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Implements the committed decision pricing_api v2 and follows money.representation v1
(money as int cents, percentages as percent numbers) and customer.unknown_signal v1
(KeyError on unknown lookups).

Public API:
  get_item(sku)             -> Item (KeyError if sku unknown)
  get_customer(customer_id) -> Customer (KeyError if id unknown)
  list_items()              -> list[Item]     (catalog order)
  list_customers()          -> list[Customer] (file order)

Item:     sku: str, name: str, price_cents: int, category: str
Customer: id: str, name: str, discount_pct: number (10 = 10%, 0 if none), region: str
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
    price_cents: int  # int cents, e.g. 1250 means $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount_pct: float  # percent number, e.g. 10 means 10% off; 0 if none
    region: str          # e.g. "TX"; passed to tax.compute_tax, which decides tax rules


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_items():
    items = {}
    for row in _read_csv(_CATALOG_PATH):
        sku = row["sku"].strip()
        if sku in items:
            raise ValueError(f"duplicate SKU in catalog.csv: {sku!r}")
        items[sku] = Item(
            sku=sku,
            name=row["name"].strip(),
            price_cents=int(row["price_cents"]),
            category=row["category"].strip(),
        )
    return items


def _parse_percent(text):
    """Parse a percent number such as '10' or '8.25' into int or float (not a fraction)."""
    text = text.strip()
    value = float(text)
    return int(value) if value.is_integer() else value


def _load_customers():
    customers = {}
    for row in _read_csv(_CUSTOMERS_PATH):
        cid = row["id"].strip()
        if cid in customers:
            raise ValueError(f"duplicate customer id in customers.csv: {cid!r}")
        customers[cid] = Customer(
            id=cid,
            name=row["name"].strip(),
            discount_pct=_parse_percent(row["discount_pct"]),
            region=row["region"].strip(),
        )
    return customers


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return the Item with this SKU. Raises KeyError if the SKU is unknown."""
    return _ITEMS[sku]


def get_customer(customer_id):
    """Return the Customer with this id. Raises KeyError if the id is unknown."""
    return _CUSTOMERS[customer_id]


def list_items():
    """Return all items in catalog order."""
    return list(_ITEMS.values())


def list_customers():
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())
