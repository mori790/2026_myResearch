"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Public API (all money amounts are integer cents):

    get_item(sku) -> Item
    list_items() -> list[Item]
    get_customer(customer_id) -> Customer
    list_customers() -> list[Customer]
    discount_cents(customer_id, amount_cents) -> int
        Discount amount for a subtotal, using the customer's discount_pct.
        Rounded half-up to the nearest cent.
    line_pricing(sku, quantity, customer_id) -> LinePricing
        Unit price, gross, discount and net amount for one invoice line.
        Tax is NOT computed here; the caller passes net_cents and the
        customer's region to tax.py.

Errors:
    UnknownSKUError, UnknownCustomerError  (both subclass KeyError)
    PricingDataError                       (malformed data files)
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from typing import Dict, List

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


class PricingDataError(ValueError):
    """Raised when a data file is missing a column or contains invalid values."""


class UnknownSKUError(KeyError):
    """Raised when a SKU is not in the catalog."""


class UnknownCustomerError(KeyError):
    """Raised when a customer id is not in the customer table."""


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


@dataclass(frozen=True)
class LinePricing:
    sku: str
    quantity: int
    unit_price_cents: int
    gross_cents: int     # unit_price_cents * quantity
    discount_cents: int  # customer discount on gross_cents
    net_cents: int       # gross_cents - discount_cents (taxable amount)


def _require_columns(path: str, reader: csv.DictReader, required: List[str]) -> None:
    fields = reader.fieldnames or []
    missing = [c for c in required if c not in fields]
    if missing:
        raise PricingDataError(f"{path}: missing column(s): {', '.join(missing)}")


def _parse_int(path: str, row_no: int, column: str, value: str, low: int, high: int) -> int:
    try:
        number = int(value.strip())
    except (ValueError, AttributeError):
        raise PricingDataError(f"{path}: line {row_no}: {column} must be an integer, got {value!r}")
    if not (low <= number <= high):
        raise PricingDataError(
            f"{path}: line {row_no}: {column} must be in [{low}, {high}], got {number}"
        )
    return number


@lru_cache(maxsize=1)
def _load_catalog() -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        _require_columns(_CATALOG_PATH, reader, ["sku", "name", "price_cents", "category"])
        for row_no, row in enumerate(reader, start=2):
            sku = row["sku"].strip()
            if not sku:
                raise PricingDataError(f"{_CATALOG_PATH}: line {row_no}: empty sku")
            if sku in items:
                raise PricingDataError(f"{_CATALOG_PATH}: line {row_no}: duplicate sku {sku!r}")
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                price_cents=_parse_int(_CATALOG_PATH, row_no, "price_cents", row["price_cents"], 0, 10**12),
                category=row["category"].strip(),
            )
    return items


@lru_cache(maxsize=1)
def _load_customers() -> Dict[str, Customer]:
    customers: Dict[str, Customer] = {}
    with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        _require_columns(_CUSTOMERS_PATH, reader, ["id", "name", "discount_pct", "region"])
        for row_no, row in enumerate(reader, start=2):
            cid = row["id"].strip()
            if not cid:
                raise PricingDataError(f"{_CUSTOMERS_PATH}: line {row_no}: empty id")
            if cid in customers:
                raise PricingDataError(f"{_CUSTOMERS_PATH}: line {row_no}: duplicate id {cid!r}")
            customers[cid] = Customer(
                id=cid,
                name=row["name"].strip(),
                discount_pct=_parse_int(_CUSTOMERS_PATH, row_no, "discount_pct", row["discount_pct"], 0, 100),
                region=row["region"].strip(),
            )
    return customers


def get_item(sku: str) -> Item:
    """Return the catalog entry for `sku`. Raises UnknownSKUError if absent."""
    try:
        return _load_catalog()[sku]
    except KeyError:
        raise UnknownSKUError(sku) from None


def list_items() -> List[Item]:
    """All catalog items, in file order."""
    return list(_load_catalog().values())


def get_customer(customer_id: str) -> Customer:
    """Return the customer record for `customer_id`. Raises UnknownCustomerError if absent."""
    try:
        return _load_customers()[customer_id]
    except KeyError:
        raise UnknownCustomerError(customer_id) from None


def list_customers() -> List[Customer]:
    """All customer records, in file order."""
    return list(_load_customers().values())


def discount_cents(customer_id: str, amount_cents: int) -> int:
    """Discount for `amount_cents` at the customer's discount_pct, rounded half-up to a cent."""
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents < 0:
        raise ValueError(f"amount_cents must be a non-negative int, got {amount_cents!r}")
    pct = get_customer(customer_id).discount_pct
    exact = Decimal(amount_cents) * Decimal(pct) / Decimal(100)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def line_pricing(sku: str, quantity: int, customer_id: str) -> LinePricing:
    """Price one invoice line: unit price x quantity, minus the customer's discount.

    Tax is intentionally not computed here.
    """
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"quantity must be a positive int, got {quantity!r}")
    item = get_item(sku)
    get_customer(customer_id)  # validates the customer exists
    gross = item.price_cents * quantity
    disc = discount_cents(customer_id, gross)
    return LinePricing(
        sku=sku,
        quantity=quantity,
        unit_price_cents=item.price_cents,
        gross_cents=gross,
        discount_cents=disc,
        net_cents=gross - disc,
    )
