"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
- Money amounts are floats in dollars (12.5 means $12.50).
- Percentages are fractions (10% is 0.10).
- A lookup that finds nothing returns None.

Public API:
- get_item(sku) -> Item | None
- get_customer(customer_id) -> Customer | None
- list_items() -> list[Item]
- list_customers() -> list[Customer]
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from typing import Optional

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price: float  # dollars, e.g. 12.5 means $12.50
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount: float  # fraction, e.g. 0.10 means 10% off
    region: str


_items: Optional[dict] = None
_customers: Optional[dict] = None


def _read_csv(path: str) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()}
                for row in csv.DictReader(f)]


def _load_items() -> dict:
    global _items
    if _items is None:
        items = {}
        for row in _read_csv(_CATALOG_PATH):
            sku = row["sku"]
            if sku in items:
                raise ValueError(f"duplicate sku in catalog.csv: {sku!r}")
            items[sku] = Item(
                sku=sku,
                name=row["name"],
                price=int(row["price_cents"]) / 100.0,
                category=row["category"],
            )
        _items = items
    return _items


def _load_customers() -> dict:
    global _customers
    if _customers is None:
        customers = {}
        for row in _read_csv(_CUSTOMERS_PATH):
            cid = row["id"]
            if cid in customers:
                raise ValueError(f"duplicate id in customers.csv: {cid!r}")
            customers[cid] = Customer(
                id=cid,
                name=row["name"],
                discount=float(row["discount_pct"]) / 100.0,
                region=row["region"],
            )
        _customers = customers
    return _customers


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with the given SKU, or None if it does not exist."""
    return _load_items().get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with the given id, or None if it does not exist."""
    return _load_customers().get(customer_id)


def list_items() -> list:
    """Return all items, in catalog order."""
    return list(_load_items().values())


def list_customers() -> list:
    """Return all customers, in file order."""
    return list(_load_customers().values())
