"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Data files live in data_pricing/ next to this file:
  catalog.csv    : sku, name, price_cents, category
  customers.csv  : id, name, discount_pct, region

Public API (committed decision pricing_api v2, pricing_missing v1):
  get_item(sku)                -> dict | None
      keys: sku (str), name (str), price_cents (int, exact cents before discount),
            price (float, dollars before discount, same value as price_cents / 100),
            category (str)
  get_customer(customer_id)    -> dict | None
      keys: id (str), name (str), discount (float fraction, 0.10 = 10%; 0.0 if none),
            region (str, state code as in data, e.g. "TX")

Lookups return None when the sku or customer id is not found.
Money is float dollars in `price`; integer cents in `price_cents` are the exact value
for arithmetic. Percentages in the data (discount_pct, 10 = 10%) are converted to
fractions on load.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            price_cents = int(row["price_cents"].strip())
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price_cents": price_cents,
                "price": price_cents / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            discount_pct = float(row["discount_pct"].strip())
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount": discount_pct / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return a copy of the item record for `sku`, or None if the sku is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
