"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

The data files are in data_pricing/ next to this file.

API (committed decision `pricing_api` v1):
    get_item(sku: str) -> Item
        Item(sku: str, name: str, price_cents: int, category: str)
        Raises UnknownSKU (a KeyError subclass) if the SKU does not exist.

    get_customer(customer_id: str) -> Customer
        Customer(id: str, name: str, discount_pct: int, region: str)
        Raises UnknownCustomer (a KeyError subclass) if the ID does not exist.

    discounted_price_cents(unit_price_cents: int, discount_pct: int) -> int
        Price after the percent discount, in integer cents, rounded half-up.

All money is integer cents. This module contains no tax logic.
"""

import csv
import os
from dataclasses import dataclass

__all__ = [
    "Item",
    "Customer",
    "UnknownSKU",
    "UnknownCustomer",
    "get_item",
    "get_customer",
    "discounted_price_cents",
]

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


class UnknownSKU(KeyError):
    """Raised by get_item when the SKU is not in the catalog."""


class UnknownCustomer(KeyError):
    """Raised by get_customer when the customer ID is not in the customer file."""


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
    discount_pct: int
    region: str


def _parse_pct(value: str, where: str) -> int:
    pct = int(value.strip())
    if not 0 <= pct <= 100:
        raise ValueError(f"{where}: discount_pct must be 0-100, got {pct}")
    return pct


def _load_catalog(path: str) -> dict:
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"{path}: duplicate sku {sku!r}")
            price_cents = int(row["price_cents"].strip())
            if price_cents < 0:
                raise ValueError(f"{path}: negative price for sku {sku!r}")
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                price_cents=price_cents,
                category=row["category"].strip(),
            )
    return items


def _load_customers(path: str) -> dict:
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"{path}: duplicate customer id {cid!r}")
            customers[cid] = Customer(
                id=cid,
                name=row["name"].strip(),
                discount_pct=_parse_pct(row["discount_pct"], f"{path} id {cid!r}"),
                region=row["region"].strip(),
            )
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku: str) -> Item:
    try:
        return _ITEMS[sku]
    except KeyError:
        raise UnknownSKU(sku) from None


def get_customer(customer_id: str) -> Customer:
    try:
        return _CUSTOMERS[customer_id]
    except KeyError:
        raise UnknownCustomer(customer_id) from None


def discounted_price_cents(unit_price_cents: int, discount_pct: int) -> int:
    """Return unit_price_cents minus discount_pct percent, in integer cents.

    The discount amount is unit_price_cents * discount_pct / 100, rounded
    half-up to the nearest cent. The result is the price after the discount.
    Uses integer arithmetic only, so no floating-point rounding errors.
    """
    if not 0 <= discount_pct <= 100:
        raise ValueError(f"discount_pct must be 0-100, got {discount_pct}")
    if unit_price_cents < 0:
        raise ValueError(f"unit_price_cents must be non-negative, got {unit_price_cents}")
    discount_cents = (unit_price_cents * discount_pct + 50) // 100
    return unit_price_cents - discount_cents
