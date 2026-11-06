"""Item and customer information for the invoicing package.

Owned by agent1 (pricing). Data files live in data_pricing/ next to this module.

Agreed interface (decision log topic: pricing_api, v2):
  get_item(sku)                -> {"sku", "name", "price", "category"} or None
  get_customer(customer_id)    -> {"id", "name", "discount", "region"} or None

Conventions (team standard):
  * money  = float in dollars (12.5 means $12.50)
  * percent = float fraction OFF (0.10 means 10% off, 0.0 means no discount)
  * a lookup that finds nothing returns None

Raw data is stored as integer cents (catalog.csv: price_cents) and whole
percents (customers.csv: discount_pct). Conversion happens here, at the
boundary, so callers never see the raw units.
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
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # integer cents -> float dollars (e.g. 1250 -> 12.5)
                "price": int(row["price_cents"]) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # whole percent -> fraction (e.g. 10 -> 0.10)
                "discount": int(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
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
