"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Conventions (team standard):
  - Money amounts are floats in dollars (12.5 means $12.50).
  - Percentages are fractions (10% is 0.10).
  - A lookup that finds nothing returns None.

Data files are in data_pricing/ next to this file:
  - catalog.csv   : sku, name, price_cents, category   (stored in cents, exposed in dollars)
  - customers.csv : id, name, discount_pct, region     (stored as whole percent, exposed as fraction)

Public API:
  get_item(sku)              -> Item | None
  get_customer(customer_id)  -> Customer | None
  list_items()               -> list[Item]     (catalog order)
  list_customers()           -> list[Customer] (file order)
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_FILE = _DATA_DIR / "catalog.csv"
_CUSTOMERS_FILE = _DATA_DIR / "customers.csv"


@dataclass(frozen=True)
class Item:
    """A catalog item.

    price: unit price in dollars (float), e.g. 12.5 means $12.50.
    """

    sku: str
    name: str
    price: float
    category: str


@dataclass(frozen=True)
class Customer:
    """A customer record.

    discount_rate: customer discount as a fraction, e.g. 0.10 means 10% off.
    region: region code as given in the data file (e.g. "TX").
    """

    id: str
    name: str
    discount_rate: float
    region: str


def _cents_to_dollars(cents_text: str) -> float:
    return round(int(cents_text.strip()) / 100, 2)


def _percent_to_fraction(pct_text: str) -> float:
    return round(float(pct_text.strip()) / 100, 6)


@lru_cache(maxsize=1)
def _load_items() -> tuple[tuple[Item, ...], dict[str, Item]]:
    items: list[Item] = []
    by_sku: dict[str, Item] = {}
    with _CATALOG_FILE.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in by_sku:
                raise ValueError(f"duplicate sku in {_CATALOG_FILE.name}: {sku!r}")
            item = Item(
                sku=sku,
                name=row["name"].strip(),
                price=_cents_to_dollars(row["price_cents"]),
                category=row["category"].strip(),
            )
            items.append(item)
            by_sku[sku] = item
    return tuple(items), by_sku


@lru_cache(maxsize=1)
def _load_customers() -> tuple[tuple[Customer, ...], dict[str, Customer]]:
    customers: list[Customer] = []
    by_id: dict[str, Customer] = {}
    with _CUSTOMERS_FILE.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in by_id:
                raise ValueError(f"duplicate customer id in {_CUSTOMERS_FILE.name}: {cid!r}")
            customer = Customer(
                id=cid,
                name=row["name"].strip(),
                discount_rate=_percent_to_fraction(row["discount_pct"]),
                region=row["region"].strip(),
            )
            customers.append(customer)
            by_id[cid] = customer
    return tuple(customers), by_id


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with this SKU, or None if there is no such SKU."""
    _, by_sku = _load_items()
    return by_sku.get(sku)


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with this id, or None if there is no such customer."""
    _, by_id = _load_customers()
    return by_id.get(customer_id)


def list_items() -> list[Item]:
    """Return all catalog items in catalog order."""
    items, _ = _load_items()
    return list(items)


def list_customers() -> list[Customer]:
    """Return all customers in file order."""
    customers, _ = _load_customers()
    return list(customers)
