"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Implements the committed decision ``pricing_api`` (v1) from the shared agreement log:

    All money is integer cents (int) at module boundaries.
    get_item(sku)                -> Item(sku, name, price_cents, category)
                                    raises UnknownItemError (a KeyError subclass) if unknown.
    get_customer(customer_id)    -> Customer(id, name, discount_percent, region)
                                    discount_percent is an int, 10 means 10%.
                                    raises UnknownCustomerError (a KeyError subclass) if unknown.
    list_items()                 -> list[Item], in file order
    list_customers()             -> list[Customer], in file order

This module does NO discount or tax arithmetic. invoice.py does discount math,
and tax.py does tax math.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

__all__ = [
    "Item",
    "Customer",
    "PricingError",
    "UnknownItemError",
    "UnknownCustomerError",
    "get_item",
    "get_customer",
    "list_items",
    "list_customers",
]

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_FILE = _DATA_DIR / "catalog.csv"
_CUSTOMERS_FILE = _DATA_DIR / "customers.csv"


class PricingError(Exception):
    """Base class for pricing data errors."""


class UnknownItemError(PricingError, KeyError):
    """Raised by get_item() when the SKU is not in the catalog."""


class UnknownCustomerError(PricingError, KeyError):
    """Raised by get_customer() when the customer id is not in customers.csv."""


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price_cents: int
    category: str


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount_percent: int  # 10 means 10%
    region: str            # e.g. "TX", "OR", "NY"


def _read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@lru_cache(maxsize=1)
def _load_catalog() -> tuple[tuple[Item, ...], dict[str, Item]]:
    items: list[Item] = []
    by_sku: dict[str, Item] = {}
    for row in _read_rows(_CATALOG_FILE):
        sku = row["sku"].strip()
        price = int(row["price_cents"])
        if price < 0:
            raise PricingError(f"negative price for SKU {sku!r}: {price}")
        if sku in by_sku:
            raise PricingError(f"duplicate SKU {sku!r} in catalog.csv")
        item = Item(
            sku=sku,
            name=row["name"].strip(),
            price_cents=price,
            category=row["category"].strip(),
        )
        items.append(item)
        by_sku[sku] = item
    return tuple(items), by_sku


@lru_cache(maxsize=1)
def _load_customers() -> tuple[tuple[Customer, ...], dict[str, Customer]]:
    customers: list[Customer] = []
    by_id: dict[str, Customer] = {}
    for row in _read_rows(_CUSTOMERS_FILE):
        cid = row["id"].strip()
        pct = int(row["discount_pct"])
        if not 0 <= pct <= 100:
            raise PricingError(f"discount_pct out of range for customer {cid!r}: {pct}")
        if cid in by_id:
            raise PricingError(f"duplicate customer id {cid!r} in customers.csv")
        customer = Customer(
            id=cid,
            name=row["name"].strip(),
            discount_percent=pct,
            region=row["region"].strip(),
        )
        customers.append(customer)
        by_id[cid] = customer
    return tuple(customers), by_id


def get_item(sku: str) -> Item:
    """Return the catalog entry for ``sku``. Raises UnknownItemError if it does not exist."""
    _, by_sku = _load_catalog()
    try:
        return by_sku[sku]
    except KeyError:
        raise UnknownItemError(f"unknown SKU: {sku!r}") from None


def get_customer(customer_id: str) -> Customer:
    """Return the customer record for ``customer_id``. Raises UnknownCustomerError if unknown."""
    _, by_id = _load_customers()
    try:
        return by_id[customer_id]
    except KeyError:
        raise UnknownCustomerError(f"unknown customer id: {customer_id!r}") from None


def list_items() -> list[Item]:
    """All catalog items, in file order."""
    items, _ = _load_catalog()
    return list(items)


def list_customers() -> list[Customer]:
    """All customers, in file order."""
    customers, _ = _load_customers()
    return list(customers)
