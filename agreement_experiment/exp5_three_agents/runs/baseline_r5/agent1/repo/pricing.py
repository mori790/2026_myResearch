"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Money is always handled as integer cents to avoid floating-point rounding errors.
This module does NOT compute tax; that belongs to tax.py.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

__all__ = [
    "Item",
    "Customer",
    "UnknownSKU",
    "UnknownCustomer",
    "get_item",
    "get_customer",
    "list_items",
    "list_customers",
    "discounted_unit_price_cents",
]

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
_CATALOG_FILE = _DATA_DIR / "catalog.csv"
_CUSTOMERS_FILE = _DATA_DIR / "customers.csv"


class UnknownSKU(KeyError):
    """Raised when a SKU is not in the catalog."""


class UnknownCustomer(KeyError):
    """Raised when a customer id is not known."""


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
    discount_pct: int  # whole percent, 0..100
    region: str  # e.g. "TX", "OR", "NY"; passed through as data


def _load_items() -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    with open(_CATALOG_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate SKU in catalog: {sku!r}")
            price = int(row["price_cents"])
            if price < 0:
                raise ValueError(f"negative price for SKU {sku!r}")
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                price_cents=price,
                category=row["category"].strip(),
            )
    return items


def _load_customers() -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    with open(_CUSTOMERS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id: {cid!r}")
            pct = int(row["discount_pct"])
            if not 0 <= pct <= 100:
                raise ValueError(f"discount_pct out of range for {cid!r}: {pct}")
            customers[cid] = Customer(
                id=cid,
                name=row["name"].strip(),
                discount_pct=pct,
                region=row["region"].strip(),
            )
    return customers


# Loaded once at import time; the data files are small.
_ITEMS: Dict[str, Item] = _load_items()
_CUSTOMERS: Dict[str, Customer] = _load_customers()


def get_item(sku: str) -> Item:
    """Return the Item for ``sku``. Raises UnknownSKU if it is not in the catalog."""
    try:
        return _ITEMS[sku]
    except KeyError:
        raise UnknownSKU(sku) from None


def get_customer(customer_id: str) -> Customer:
    """Return the Customer for ``customer_id``. Raises UnknownCustomer if unknown."""
    try:
        return _CUSTOMERS[customer_id]
    except KeyError:
        raise UnknownCustomer(customer_id) from None


def list_items() -> List[Item]:
    """All catalog items, in file order."""
    return list(_ITEMS.values())


def list_customers() -> List[Customer]:
    """All customers, in file order."""
    return list(_CUSTOMERS.values())


def discounted_unit_price_cents(customer_id: str, sku: str) -> int:
    """Unit price in cents for ``sku`` after the customer's percentage discount.

    The discount is applied with integer arithmetic and rounded half-up to the
    nearest cent, e.g. 1250 cents with a 10% discount -> 1125 cents,
    705 cents with a 15% discount -> 599 cents (599.25 rounds down),
    35 cents with a 5% discount -> 33 cents (33.25 rounds down).
    Tax is NOT included.
    """
    customer = get_customer(customer_id)
    item = get_item(sku)
    # price * (100 - pct) / 100, rounded half-up. All values are non-negative.
    numerator = item.price_cents * (100 - customer.discount_pct)
    return (numerator + 50) // 100
