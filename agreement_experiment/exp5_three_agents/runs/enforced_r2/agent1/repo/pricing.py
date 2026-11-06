"""Item and customer pricing data for the invoicing package.

Implements the committed decision `pricing_api` v1:

* All money amounts are integer cents. Floats are never used for money.
* Items are loaded from data_pricing/catalog.csv and customers from
  data_pricing/customers.csv, resolved relative to this file.
* Unknown SKUs or customer ids raise KeyError.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass

__all__ = [
    "Item",
    "Customer",
    "get_item",
    "get_customer",
    "discount_cents",
    "line_total_cents",
]

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


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
    discount_pct: int  # integer percent, 0..100
    region: str


def _load_items(path: str) -> dict[str, Item]:
    items: dict[str, Item] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"]
            if sku in items:
                raise ValueError(f"duplicate sku in {path}: {sku!r}")
            items[sku] = Item(
                sku=sku,
                name=row["name"],
                price_cents=int(row["price_cents"]),
                category=row["category"],
            )
    return items


def _load_customers(path: str) -> dict[str, Customer]:
    customers: dict[str, Customer] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"]
            if cid in customers:
                raise ValueError(f"duplicate customer id in {path}: {cid!r}")
            pct = int(row["discount_pct"])
            if not 0 <= pct <= 100:
                raise ValueError(f"discount_pct out of range for {cid!r}: {pct}")
            customers[cid] = Customer(
                id=cid,
                name=row["name"],
                discount_pct=pct,
                region=row["region"],
            )
    return customers


_ITEMS: dict[str, Item] = _load_items(_CATALOG_PATH)
_CUSTOMERS: dict[str, Customer] = _load_customers(_CUSTOMERS_PATH)


def get_item(sku: str) -> Item:
    """Return the item for `sku` (case-sensitive). Raises KeyError if unknown."""
    return _ITEMS[sku]


def get_customer(customer_id: str) -> Customer:
    """Return the customer for `customer_id`. Raises KeyError if unknown."""
    return _CUSTOMERS[customer_id]


def _require_int(name: str, value: object) -> int:
    # bool is a subclass of int; reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    return value


def discount_cents(subtotal_cents: int, customer_id: str) -> int:
    """Discount amount in cents for `subtotal_cents` at the customer's rate.

    Computes round-half-up(subtotal_cents * discount_pct / 100) with integer
    arithmetic. Returns 0 when discount_pct is 0. Raises KeyError if the
    customer is unknown and ValueError if subtotal_cents is negative.
    """
    subtotal = _require_int("subtotal_cents", subtotal_cents)
    if subtotal < 0:
        raise ValueError(f"subtotal_cents must be >= 0, got {subtotal}")
    pct = _CUSTOMERS[customer_id].discount_pct
    return (subtotal * pct + 50) // 100


def line_total_cents(sku: str, qty: int) -> int:
    """Price of `qty` units of `sku` in cents. Raises KeyError if the SKU is
    unknown and ValueError if qty is negative."""
    quantity = _require_int("qty", qty)
    if quantity < 0:
        raise ValueError(f"qty must be >= 0, got {quantity}")
    return _ITEMS[sku].price_cents * quantity
