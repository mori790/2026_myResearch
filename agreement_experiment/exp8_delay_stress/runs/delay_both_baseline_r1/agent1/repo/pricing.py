"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (team standard):
- Money amounts are floats in dollars (12.5 means $12.50).
- Percentages are fractions (10% is 0.10).
- A lookup that finds nothing returns None.

This module only reports item and customer data. It does NOT apply discounts
or sales tax; callers use Customer.discount and Customer.region for that.
"""

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_FILE = _DATA_DIR / "catalog.csv"
_CUSTOMERS_FILE = _DATA_DIR / "customers.csv"


@dataclass(frozen=True)
class Item:
    """A catalog item. price is the pre-discount unit price in dollars."""

    sku: str
    name: str
    price: float
    category: str


@dataclass(frozen=True)
class Customer:
    """A customer. discount is a fraction (0.10 = 10%); region is e.g. 'TX'."""

    id: str
    name: str
    discount: float
    region: str


def _read_rows(path: Path):
    """Read a CSV file into a list of dicts with whitespace-stripped values."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            {key.strip(): (value or "").strip() for key, value in row.items()}
            for row in reader
        ]


@lru_cache(maxsize=None)
def _load_items() -> dict:
    items = {}
    for row in _read_rows(_CATALOG_FILE):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate sku in {_CATALOG_FILE.name}: {sku!r}")
        # price_cents is an integer number of cents; convert to dollars.
        price = int(row["price_cents"]) / 100
        items[sku] = Item(
            sku=sku,
            name=row["name"],
            price=price,
            category=row["category"],
        )
    return items


@lru_cache(maxsize=None)
def _load_customers() -> dict:
    customers = {}
    for row in _read_rows(_CUSTOMERS_FILE):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate customer id in {_CUSTOMERS_FILE.name}: {cid!r}")
        # discount_pct is a percentage (10 means 10%); convert to a fraction.
        discount = float(row["discount_pct"]) / 100
        customers[cid] = Customer(
            id=cid,
            name=row["name"],
            discount=discount,
            region=row["region"],
        )
    return customers


def get_item(sku: str) -> Item | None:
    """Return the Item with this SKU, or None if there is no such item."""
    return _load_items().get(sku)


def get_customer(customer_id: str) -> Customer | None:
    """Return the Customer with this id, or None if there is no such customer."""
    return _load_customers().get(customer_id)


def list_items() -> list[Item]:
    """Return all catalog items in file order."""
    return list(_load_items().values())


def list_customers() -> list[Customer]:
    """Return all customers in file order."""
    return list(_load_customers().values())
