"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Public API (all money values are integer cents):

    Item(sku, name, price_cents, category)
    Customer(id, name, discount_pct, region)

    get_item(sku)                 -> Item        (raises UnknownItemError)
    get_customer(customer_id)     -> Customer    (raises UnknownCustomerError)
    list_items()                  -> list[Item]  (catalog order)
    list_customers()              -> list[Customer] (file order)
    discount_amount_cents(unit_price_cents, discount_pct) -> int
    unit_price_after_discount_cents(sku, customer_id)     -> int
    line_total_cents(sku, quantity, customer_id)           -> int

Rounding rule for discounts: the discount amount is rounded half-up to the
nearest cent per unit price, then subtracted. Line totals are
unit_price_after_discount * quantity (no further rounding).
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


class PricingError(Exception):
    """Base class for pricing data errors."""


class UnknownItemError(PricingError, KeyError):
    """Raised when a SKU is not in the catalog."""


class UnknownCustomerError(PricingError, KeyError):
    """Raised when a customer id is not in the customer list."""


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


def _read_rows(path: str, required: List[str]) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in required if reader.fieldnames is None or c not in reader.fieldnames]
        if missing:
            raise PricingError(f"{path}: missing columns {missing}")
        rows = []
        for lineno, row in enumerate(reader, start=2):
            cleaned = {k: (v or "").strip() for k, v in row.items() if k is not None}
            if any(cleaned.get(c, "") == "" for c in required):
                raise PricingError(f"{path}:{lineno}: empty required field")
            rows.append(cleaned)
        return rows


def _load_items(path: str = _CATALOG_PATH) -> List[Item]:
    items: List[Item] = []
    seen = set()
    for row in _read_rows(path, ["sku", "name", "price_cents", "category"]):
        sku = row["sku"]
        if sku in seen:
            raise PricingError(f"{path}: duplicate sku {sku!r}")
        seen.add(sku)
        try:
            price = int(row["price_cents"])
        except ValueError:
            raise PricingError(f"{path}: price_cents for {sku!r} is not an integer") from None
        if price < 0:
            raise PricingError(f"{path}: negative price for {sku!r}")
        items.append(Item(sku=sku, name=row["name"], price_cents=price, category=row["category"]))
    return items


def _load_customers(path: str = _CUSTOMERS_PATH) -> List[Customer]:
    customers: List[Customer] = []
    seen = set()
    for row in _read_rows(path, ["id", "name", "discount_pct", "region"]):
        cid = row["id"]
        if cid in seen:
            raise PricingError(f"{path}: duplicate customer id {cid!r}")
        seen.add(cid)
        try:
            pct = int(row["discount_pct"])
        except ValueError:
            raise PricingError(f"{path}: discount_pct for {cid!r} is not an integer") from None
        if not 0 <= pct <= 100:
            raise PricingError(f"{path}: discount_pct for {cid!r} out of range 0..100")
        customers.append(Customer(id=cid, name=row["name"], discount_pct=pct, region=row["region"]))
    return customers


_ITEMS: List[Item] = _load_items()
_ITEMS_BY_SKU: Dict[str, Item] = {i.sku: i for i in _ITEMS}
_CUSTOMERS: List[Customer] = _load_customers()
_CUSTOMERS_BY_ID: Dict[str, Customer] = {c.id: c for c in _CUSTOMERS}


def get_item(sku: str) -> Item:
    try:
        return _ITEMS_BY_SKU[sku]
    except KeyError:
        raise UnknownItemError(f"unknown sku: {sku!r}") from None


def get_customer(customer_id: str) -> Customer:
    try:
        return _CUSTOMERS_BY_ID[customer_id]
    except KeyError:
        raise UnknownCustomerError(f"unknown customer id: {customer_id!r}") from None


def list_items() -> List[Item]:
    return list(_ITEMS)


def list_customers() -> List[Customer]:
    return list(_CUSTOMERS)


def discount_amount_cents(unit_price_cents: int, discount_pct: int) -> int:
    """Discount in cents for one unit, rounded half-up to the nearest cent."""
    if not 0 <= discount_pct <= 100:
        raise ValueError(f"discount_pct out of range: {discount_pct}")
    exact = Decimal(unit_price_cents) * Decimal(discount_pct) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def unit_price_after_discount_cents(sku: str, customer_id: str) -> int:
    item = get_item(sku)
    customer = get_customer(customer_id)
    return item.price_cents - discount_amount_cents(item.price_cents, customer.discount_pct)


def line_total_cents(sku: str, quantity: int, customer_id: str) -> int:
    if quantity < 0:
        raise ValueError(f"quantity must be non-negative: {quantity}")
    return unit_price_after_discount_cents(sku, customer_id) * quantity
