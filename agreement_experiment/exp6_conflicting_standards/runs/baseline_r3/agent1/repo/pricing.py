"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team coding standard (applied here):
- Money amounts are floats in dollars (12.5 means $12.50).
- Percentages are fractions (10% is 0.10).
- A lookup that finds nothing returns None.

Raw data files store money as integer cents (price_cents) and discounts as
integer percents (discount_pct). Conversion to the team standard happens once,
at load time, so callers never see cents or whole-number percents.

Public API:
    get_item(sku)            -> Item or None
    get_customer(customer_id) -> Customer or None
    list_items()             -> list of Item (in catalog file order)
    list_customers()         -> list of Customer (in customer file order)
"""

import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_FILE = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_FILE = os.path.join(_DATA_DIR, "customers.csv")


@dataclass(frozen=True)
class Item:
    """A catalog item.

    sku:      unique item code (string), e.g. "A"
    name:     display name, e.g. "Notebook"
    price:    unit price in dollars (float), e.g. 12.5 means $12.50
    category: category label, e.g. "stationery"
    """

    sku: str
    name: str
    price: float
    category: str


@dataclass(frozen=True)
class Customer:
    """A customer.

    customer_id: unique customer code (string), e.g. "C1"
    name:        display name
    discount:    customer's discount as a fraction (0.10 means 10% off)
    region:      region code, e.g. "TX"
    """

    customer_id: str
    name: str
    discount: float
    region: str


def _read_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()}
                for row in csv.DictReader(f)]


def _load_items(path: str) -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    for row in _read_rows(path):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate sku in {path}: {sku!r}")
        items[sku] = Item(
            sku=sku,
            name=row["name"],
            price=round(int(row["price_cents"]) / 100, 2),
            category=row["category"],
        )
    return items


def _load_customers(path: str) -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    for row in _read_rows(path):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate customer id in {path}: {cid!r}")
        customers[cid] = Customer(
            customer_id=cid,
            name=row["name"],
            discount=int(row["discount_pct"]) / 100,
            region=row["region"],
        )
    return customers


_ITEMS: Dict[str, Item] = _load_items(_CATALOG_FILE)
_CUSTOMERS: Dict[str, Customer] = _load_customers(_CUSTOMERS_FILE)


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with this SKU, or None if there is no such item."""
    return _ITEMS.get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with this id, or None if there is no such customer."""
    return _CUSTOMERS.get(customer_id)


def list_items() -> List[Item]:
    """Return all catalog items in file order."""
    return list(_ITEMS.values())


def list_customers() -> List[Customer]:
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())
