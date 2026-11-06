"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Team conventions (followed here):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Public API:
  get_item(sku: str) -> Item | None
  get_customer(customer_id: str) -> Customer | None
  list_items() -> list[Item]          (in catalog file order)
  list_customers() -> list[Customer]  (in customer file order)

Raw data notes (converted at load time, so callers never see raw units):
  * catalog.csv stores price_cents (integer cents)  -> Item.price (dollars, float)
  * customers.csv stores discount_pct (e.g. 10)     -> Customer.discount (fraction, e.g. 0.10)
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent / "data_pricing"
CATALOG_PATH = DATA_DIR / "catalog.csv"
CUSTOMERS_PATH = DATA_DIR / "customers.csv"


@dataclass(frozen=True)
class Item:
    """A catalog item.

    sku:      unique item code (e.g. "A")
    name:     display name (e.g. "Notebook")
    price:    unit price in dollars (float), e.g. 12.5 means $12.50
    category: category label (e.g. "stationery")
    """

    sku: str
    name: str
    price: float
    category: str


@dataclass(frozen=True)
class Customer:
    """A customer.

    id:       unique customer code (e.g. "C1")
    name:     display name (e.g. "Alice")
    discount: customer discount as a fraction (0.10 means 10%)
    region:   region code (e.g. "TX"); used by other modules, e.g. for tax
    """

    id: str
    name: str
    discount: float
    region: str


def _load_catalog(path: Path) -> dict[str, Item]:
    items: dict[str, Item] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate sku in {path.name}: {sku!r}")
            cents = int(row["price_cents"].strip())
            items[sku] = Item(
                sku=sku,
                name=row["name"].strip(),
                price=cents / 100.0,
                category=row["category"].strip(),
            )
    return items


def _load_customers(path: Path) -> dict[str, Customer]:
    customers: dict[str, Customer] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id in {path.name}: {cid!r}")
            pct = float(row["discount_pct"].strip())
            customers[cid] = Customer(
                id=cid,
                name=row["name"].strip(),
                discount=pct / 100.0,
                region=row["region"].strip(),
            )
    return customers


_ITEMS: dict[str, Item] = _load_catalog(CATALOG_PATH)
_CUSTOMERS: dict[str, Customer] = _load_customers(CUSTOMERS_PATH)


def get_item(sku: str) -> Optional[Item]:
    """Return the Item with this sku, or None if there is no such item."""
    return _ITEMS.get(sku.strip())


def get_customer(customer_id: str) -> Optional[Customer]:
    """Return the Customer with this id, or None if there is no such customer."""
    return _CUSTOMERS.get(customer_id.strip())


def list_items() -> list[Item]:
    """Return all catalog items in file order."""
    return list(_ITEMS.values())


def list_customers() -> list[Customer]:
    """Return all customers in file order."""
    return list(_CUSTOMERS.values())
