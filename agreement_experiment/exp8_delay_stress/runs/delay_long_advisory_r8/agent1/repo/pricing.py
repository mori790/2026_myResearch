"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Conventions (committed decisions VALUE_CONVENTIONS v2 and PRICING_API v2):
- Money is decimal.Decimal dollars quantized to cents, e.g. Decimal("12.50"). Never float.
- Rates are fractions, e.g. Decimal("0.10") = 10 percent.
- Lookups that find nothing return a default (Decimal("0") for money and rates,
  "" for strings). Existence checks use has_sku() and has_customer().
"""

import csv
from decimal import Decimal
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"

_CENT = Decimal("0.01")
_ZERO = Decimal("0")

# sku -> {"name": str, "unit_price": Decimal, "category": str}
_items: dict[str, dict] = {}
# customer id -> {"name": str, "discount": Decimal, "region": str}
_customers: dict[str, dict] = {}


def _load_catalog(path: Path) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in _items:
                raise ValueError(f"duplicate sku in {path.name}: {sku!r}")
            cents = int(row["price_cents"].strip())
            if cents < 0:
                raise ValueError(f"negative price for sku {sku!r} in {path.name}")
            _items[sku] = {
                "name": row["name"].strip(),
                # cents -> dollars, exact in Decimal
                "unit_price": (Decimal(cents) * _CENT).quantize(_CENT),
                "category": row["category"].strip(),
            }


def _load_customers(path: Path) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in _customers:
                raise ValueError(f"duplicate customer id in {path.name}: {cid!r}")
            pct = Decimal(row["discount_pct"].strip())
            if not (Decimal("0") <= pct <= Decimal("100")):
                raise ValueError(f"discount_pct out of range for customer {cid!r}")
            _customers[cid] = {
                "name": row["name"].strip(),
                # percent -> fraction: 10 -> Decimal("0.10"), exact in Decimal
                "discount": pct.scaleb(-2),
                "region": row["region"].strip(),
            }


_load_catalog(_DATA_DIR / "catalog.csv")
_load_customers(_DATA_DIR / "customers.csv")


# ---- items -----------------------------------------------------------------

def has_sku(sku: str) -> bool:
    """True if sku is in the catalog."""
    return sku in _items


def get_unit_price(sku: str) -> Decimal:
    """Unit price in dollars (Decimal, cents precision). Decimal("0") if unknown."""
    item = _items.get(sku)
    return item["unit_price"] if item else _ZERO


def get_item_name(sku: str) -> str:
    """Item name. Empty string if unknown."""
    item = _items.get(sku)
    return item["name"] if item else ""


def get_item_category(sku: str) -> str:
    """Item category as in catalog.csv. Empty string if unknown."""
    item = _items.get(sku)
    return item["category"] if item else ""


# ---- customers -------------------------------------------------------------

def has_customer(customer_id: str) -> bool:
    """True if the customer exists."""
    return customer_id in _customers


def get_customer_name(customer_id: str) -> str:
    """Customer name. Empty string if unknown (invoice then shows the id)."""
    cust = _customers.get(customer_id)
    return cust["name"] if cust else ""


def get_customer_discount(customer_id: str) -> Decimal:
    """Discount as a fraction, e.g. Decimal("0.10") = 10 percent off.
    Decimal("0") (no discount) if unknown."""
    cust = _customers.get(customer_id)
    return cust["discount"] if cust else _ZERO


def get_customer_region(customer_id: str) -> str:
    """Region code as in customers.csv, e.g. "TX". Empty string if unknown."""
    cust = _customers.get(customer_id)
    return cust["region"] if cust else ""
