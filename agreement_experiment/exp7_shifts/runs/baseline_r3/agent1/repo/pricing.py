"""Item and customer information for the invoicing package.

Owned by agent1 (PRICING).

Team conventions (see the agreed API decision "pricing_api"):
  * Money amounts are floats in dollars (12.5 means $12.50).
  * Percentages are fractions (10% is 0.10).
  * A lookup that finds nothing returns None.

Data files live in ``data_pricing/`` next to this module:
  * catalog.csv   : sku, name, price_cents, category
  * customers.csv : id, name, discount_pct, region
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_catalog(path=_CATALOG_PATH):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                # Stored in cents in the file; exposed in dollars.
                "price": round(int(row["price_cents"]) / 100, 2),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path=_CUSTOMERS_PATH):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # Stored as a percentage number in the file; exposed as a fraction.
                "discount": round(float(row["discount_pct"]) / 100, 4),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog()
_CUSTOMERS = _load_customers()


def get_item(sku):
    """Return a copy of the item dict for ``sku``, or None if unknown.

    Keys: "sku" (str), "name" (str), "price" (float, dollars), "category" (str).
    """
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_price(sku):
    """Return the unit price in dollars for ``sku``, or None if unknown."""
    item = _ITEMS.get(sku)
    return item["price"] if item is not None else None


def list_items():
    """Return a list of copies of all item dicts, in catalog order."""
    return [dict(item) for item in _ITEMS.values()]


def get_customer(customer_id):
    """Return a copy of the customer dict for ``customer_id``, or None if unknown.

    Keys: "id" (str), "name" (str), "discount" (float fraction, e.g. 0.10
    for 10%), "region" (str).
    """
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def get_discount(customer_id):
    """Return the customer's discount as a fraction (0.10 = 10%), or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return customer["discount"] if customer is not None else None


def list_customers():
    """Return a list of copies of all customer dicts, in file order."""
    return [dict(customer) for customer in _CUSTOMERS.values()]
