"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

All money amounts are integers in cents. Prices and discounts are never floats.
Computed values (line subtotals, discounts) are exact integer arithmetic; discounts are
rounded half up to the cent.

Public API:
    get_item(sku) -> Item                          raises UnknownItemError
    get_customer(customer_id) -> Customer          raises UnknownCustomerError
    line_subtotal_cents(sku, qty) -> int           raises UnknownItemError / ValueError
    discount_cents(customer_id, subtotal_cents) -> int   raises UnknownCustomerError / ValueError
"""

import csv
import os
from dataclasses import dataclass
from typing import Dict

__all__ = [
    "Item",
    "Customer",
    "UnknownItemError",
    "UnknownCustomerError",
    "get_item",
    "get_customer",
    "line_subtotal_cents",
    "discount_cents",
]

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


class UnknownItemError(KeyError):
    """Raised when a SKU is not in the catalog."""


class UnknownCustomerError(KeyError):
    """Raised when a customer ID is not known."""


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
    region: str


def _load_catalog(path: str) -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    with open(path, newline="", encoding="utf-8") as f:
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


def _load_customers(path: str) -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer ID: {cid!r}")
            pct = int(row["discount_pct"])
            if not 0 <= pct <= 100:
                raise ValueError(f"discount_pct out of range for customer {cid!r}")
            customers[cid] = Customer(
                id=cid,
                name=row["name"].strip(),
                discount_pct=pct,
                region=row["region"].strip(),
            )
    return customers


_ITEMS: Dict[str, Item] = _load_catalog(_CATALOG_PATH)
_CUSTOMERS: Dict[str, Customer] = _load_customers(_CUSTOMERS_PATH)


def get_item(sku: str) -> Item:
    """Return the catalog entry for ``sku``. Raises UnknownItemError if absent."""
    try:
        return _ITEMS[sku]
    except KeyError:
        raise UnknownItemError(f"unknown SKU: {sku!r}") from None


def get_customer(customer_id: str) -> Customer:
    """Return the customer record for ``customer_id``. Raises UnknownCustomerError if absent."""
    try:
        return _CUSTOMERS[customer_id]
    except KeyError:
        raise UnknownCustomerError(f"unknown customer ID: {customer_id!r}") from None


def line_subtotal_cents(sku: str, qty: int) -> int:
    """Return unit price times quantity, in cents, before any customer discount."""
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError(f"quantity must be a positive integer, got {qty!r}")
    return get_item(sku).price_cents * qty


def discount_cents(customer_id: str, subtotal_cents: int) -> int:
    """Return the discount amount in cents for a pre-tax subtotal.

    The discount is subtotal * discount_pct / 100, rounded half up to the nearest cent.
    """
    if isinstance(subtotal_cents, bool) or not isinstance(subtotal_cents, int) or subtotal_cents < 0:
        raise ValueError(
            f"subtotal must be a non-negative integer number of cents, got {subtotal_cents!r}"
        )
    pct = get_customer(customer_id).discount_pct
    return (subtotal_cents * pct + 50) // 100
