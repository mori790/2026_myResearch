"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (followed here):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Public API:
  get_item(sku: str) -> Item | None
  get_customer(customer_id: str) -> Customer | None
  all_items() -> list[Item]
  all_customers() -> list[Customer]

The raw CSV files store prices in integer cents and discounts as integer
percentages (e.g. 10 means 10%). Those are converted to the team conventions
when the data is loaded, so callers never see cents or whole-number percentages.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"


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
    discount: float  # fraction, e.g. 0.10 means 10%
    region: str


def _load_items(path: Path) -> dict[str, Item]:
    items: dict[str, Item] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                price=int(row["price_cents"]) / 100,
                category=row["category"].strip(),
            )
    return items


def _load_customers(path: Path) -> dict[str, Customer]:
    customers: dict[str, Customer] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = Customer(
                id=cid,
                name=row["name"].strip(),
                discount=int(row["discount_pct"]) / 100,
                region=row["region"].strip(),
            )
    return customers


_ITEMS: dict[str, Item] = _load_items(_DATA_DIR / "catalog.csv")
_CUSTOMERS: dict[str, Customer] = _load_customers(_DATA_DIR / "customers.csv")


def get_item(sku: str) -> Item | None:
    """Return the item with the given SKU, or None if there is no such item."""
    return _ITEMS.get(sku)


def get_customer(customer_id: str) -> Customer | None:
    """Return the customer with the given ID, or None if there is no such customer."""
    return _CUSTOMERS.get(customer_id)


def all_items() -> list[Item]:
    """Return all items in catalog order."""
    return list(_ITEMS.values())


def all_customers() -> list[Customer]:
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())
