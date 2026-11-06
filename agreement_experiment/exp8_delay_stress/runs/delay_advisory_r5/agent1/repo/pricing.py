"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules.
Data files live in data_pricing/ next to this file:
  - catalog.csv   : sku, name, price_cents, category
  - customers.csv : id, name, discount_pct, region

Public API (committed as decision `pricing_api`):
  get_item(sku: str) -> dict | None
      {"sku": str, "name": str, "price": float (dollars), "category": str}
      None if the sku is unknown.
  get_customer(customer_id: str) -> dict | None
      {"id": str, "name": str, "discount": float (fraction, 0.10 = 10%), "region": str}
      None if the customer id is unknown.

Team conventions: money is a float in dollars; percentages are fractions;
a failed lookup returns None. Pricing only returns data. It does not compute
line totals, discounts, or tax.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()}
                for row in csv.DictReader(f)]


def _load_items(path):
    items = {}
    for row in _read_rows(path):
        sku = row["sku"]
        if sku in items:
            raise ValueError(f"duplicate sku {sku!r} in {path}")
        items[sku] = {
            "sku": sku,
            "name": row["name"],
            "price": round(int(row["price_cents"]) / 100, 2),  # cents -> dollars
            "category": row["category"],
        }
    return items


def _load_customers(path):
    customers = {}
    for row in _read_rows(path):
        cid = row["id"]
        if cid in customers:
            raise ValueError(f"duplicate customer id {cid!r} in {path}")
        customers[cid] = {
            "id": cid,
            "name": row["name"],
            "discount": round(float(row["discount_pct"]) / 100, 6),  # percent -> fraction
            "region": row["region"],
        }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return a copy of the item record for `sku`, or None if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
