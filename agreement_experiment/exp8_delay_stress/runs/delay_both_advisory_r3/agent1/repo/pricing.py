"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed API (decision ``pricing_api`` v1):
    get_item(sku)          -> dict {sku, name, price, category} or None
    get_customer(cust_id)  -> dict {id, name, discount, region} or None

Units: money is a float in dollars (1250 cents -> 12.5);
percentages are fractions (10 % -> 0.10). Lookups that find nothing return None.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Source stores integer cents; convert to float dollars.
                "price": int(row["price_cents"]) / 100,
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cust_id = row["id"].strip()
            customers[cust_id] = {
                "id": cust_id,
                "name": row["name"].strip(),
                # Source stores whole percent; convert to a fraction.
                "discount": float(row["discount_pct"]) / 100,
                "region": row["region"].strip().upper(),
            }
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return a copy of the item record for ``sku``, or None if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for ``customer_id``, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
