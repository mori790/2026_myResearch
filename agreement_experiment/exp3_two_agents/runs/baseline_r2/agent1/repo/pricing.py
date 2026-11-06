"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

Conventions:
- All money amounts are integer cents.
- Percentages are Decimal values (e.g. Decimal("8.25") means 8.25%).
- Rounding is half-up to the nearest cent.
"""

import csv
import os
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class UnknownSkuError(KeyError):
    """Raised when a SKU is not in the catalog."""


class UnknownCustomerError(KeyError):
    """Raised when a customer id is not in the customer list."""


class UnknownRegionError(KeyError):
    """Raised when a region has no tax rate."""


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price_cents: int


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    discount_pct: Decimal
    region: str


def _read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_catalog():
    return {
        row["sku"]: Item(
            sku=row["sku"],
            name=row["name"],
            price_cents=int(row["price_cents"]),
        )
        for row in _read_csv("catalog.csv")
    }


def _load_customers():
    return {
        row["id"]: Customer(
            id=row["id"],
            name=row["name"],
            discount_pct=Decimal(row["discount_pct"]),
            region=row["region"],
        )
        for row in _read_csv("customers.csv")
    }


def _load_tax_rates():
    return {
        row["region"]: Decimal(row["tax_pct"])
        for row in _read_csv("tax.csv")
    }


_CATALOG = _load_catalog()
_CUSTOMERS = _load_customers()
_TAX_RATES = _load_tax_rates()


def _round_cents(value):
    """Round a Decimal number of cents to an integer, half-up."""
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def get_item(sku):
    """Return the Item for a SKU. Raises UnknownSkuError if missing."""
    try:
        return _CATALOG[sku]
    except KeyError:
        raise UnknownSkuError(sku) from None


def get_customer(customer_id):
    """Return the Customer for an id. Raises UnknownCustomerError if missing."""
    try:
        return _CUSTOMERS[customer_id]
    except KeyError:
        raise UnknownCustomerError(customer_id) from None


def get_tax_pct(region):
    """Return the tax rate (percent) for a region. Raises UnknownRegionError if missing."""
    try:
        return _TAX_RATES[region]
    except KeyError:
        raise UnknownRegionError(region) from None


def line_total_cents(sku, qty):
    """Return price_cents * qty for a SKU."""
    return get_item(sku).price_cents * qty


def discount_cents(subtotal_cents, customer_id):
    """Return the discount amount in cents for a subtotal and customer."""
    pct = get_customer(customer_id).discount_pct
    return _round_cents(Decimal(subtotal_cents) * pct / Decimal(100))


def tax_cents(taxable_cents, region):
    """Return the tax amount in cents for a taxable amount in a region."""
    pct = get_tax_pct(region)
    return _round_cents(Decimal(taxable_cents) * pct / Decimal(100))
