"""Item catalog and customer lookup for the invoicing package (owner: agent1).

Implements the committed decisions ``money_and_lookup_conventions`` v2 and
``pricing_api`` v2 in the shared agreement log:

* Money crosses module boundaries as integer cents (1250 = $12.50).
* Percentages are plain numbers (10 = 10 percent).
* Lookups that find nothing return None.

Public API
----------
get_item(sku) -> dict | None
    {"sku": str, "name": str, "unit_price_cents": int, "category": str}
get_customer(customer_id) -> dict | None
    {"customer_id": str, "name": str, "discount_pct": int | Decimal,
     "region": str | None}
list_items() -> list[dict]
    All catalog items, in catalog file order, in the get_item format.

Data files are read from ``data_pricing/`` next to this module.
"""

import csv
import os
from decimal import Decimal, InvalidOperation

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _parse_number(text, where):
    """Parse a CSV number exactly. Integral values become int, others Decimal."""
    try:
        value = Decimal(text.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"{where}: not a number: {text!r}") from None
    if not value.is_finite():
        raise ValueError(f"{where}: not a finite number: {text!r}")
    if value == value.to_integral_value():
        return int(value)
    return value


def _parse_int(text, where):
    value = _parse_number(text, where)
    if not isinstance(value, int):
        raise ValueError(f"{where}: expected an integer, got {text!r}")
    return value


def _load_catalog(path):
    items = {}
    order = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for lineno, row in enumerate(reader, start=2):
            where = f"{os.path.basename(path)}:{lineno}"
            sku = row["sku"].strip()
            if not sku:
                raise ValueError(f"{where}: empty sku")
            if sku in items:
                raise ValueError(f"{where}: duplicate sku {sku!r}")
            price_cents = _parse_int(row["price_cents"], where)
            if price_cents < 0:
                raise ValueError(f"{where}: negative price_cents")
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "unit_price_cents": price_cents,
                "category": row["category"].strip(),
            }
            order.append(sku)
    return items, order


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for lineno, row in enumerate(reader, start=2):
            where = f"{os.path.basename(path)}:{lineno}"
            customer_id = row["id"].strip()
            if not customer_id:
                raise ValueError(f"{where}: empty id")
            if customer_id in customers:
                raise ValueError(f"{where}: duplicate customer id {customer_id!r}")
            discount_pct = _parse_number(row["discount_pct"], where)
            if not 0 <= discount_pct <= 100:
                raise ValueError(f"{where}: discount_pct out of range 0..100")
            region = row["region"].strip() or None
            customers[customer_id] = {
                "customer_id": customer_id,
                "name": row["name"].strip(),
                "discount_pct": discount_pct,
                "region": region,
            }
    return customers


_ITEMS, _ITEM_ORDER = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the item for ``sku`` as a new dict, or None if it is not in the catalog."""
    if sku is None:
        return None
    item = _ITEMS.get(str(sku).strip())
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer for ``customer_id`` as a new dict, or None if unknown."""
    if customer_id is None:
        return None
    customer = _CUSTOMERS.get(str(customer_id).strip())
    return dict(customer) if customer is not None else None


def list_items():
    """Return all catalog items in catalog file order, as new dicts."""
    return [dict(_ITEMS[sku]) for sku in _ITEM_ORDER]
