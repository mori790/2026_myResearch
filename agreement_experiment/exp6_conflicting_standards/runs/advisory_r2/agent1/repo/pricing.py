"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules.
Data files live in data_pricing/ next to this file:
  - catalog.csv   : sku, name, price_cents, category
  - customers.csv : id, name, discount_pct, region

Committed team decisions (agree.py log):
  - money_unit   : money amounts are floats in dollars (12.5 == $12.50).
  - percent_unit : percentages are fractions (10% == 0.10).
  - lookup_miss  : a lookup that finds nothing returns None.
  - pricing_api  : get_item(sku) and get_customer(customer_id) as below.

    get_item(sku) -> dict | None
        keys: sku (str), name (str), price (float dollars), category (str)

    get_customer(customer_id) -> dict | None
        keys: id (str), name (str), discount (float fraction), region (str)
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path):
    """Return {sku: item_dict}. The CSV stores price in integer cents; convert to float dollars."""
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price": round(int(row["price_cents"]) / 100, 2),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    """Return {customer_id: customer_dict}. The CSV stores discount as a whole percent; convert to a fraction."""
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount": round(int(row["discount_pct"]) / 100, 4),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return a copy of the item record for `sku`, or None if the SKU is unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for `customer_id`, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
