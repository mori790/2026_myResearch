"""Item and customer information for the invoicing package.

Committed interface (shared decision log, topic ``pricing_api`` v2):

* Money is a float in dollars (12.5 means $12.50). Rounding is left to the caller.
* Discounts are fractions OFF (0.10 means 10% off). A caller computes the
  multiplier as ``1 - discount``.
* A lookup that finds nothing returns ``None``.

Functions:

* ``get_item(sku)`` -> ``{"sku", "name", "price", "category"}`` or ``None``
* ``get_customer(customer_id)`` -> ``{"id", "name", "discount", "region"}`` or ``None``

Data files live in ``data_pricing/`` next to this module:

* ``catalog.csv``   columns: sku, name, price_cents, category
* ``customers.csv`` columns: id, name, discount_pct, region
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
                # Stored as integer cents in the data file; the team standard is dollars.
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
                # Stored as a whole-number percent in the data file; the team standard is a fraction.
                "discount": int(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return a copy of the item record for ``sku``, or ``None`` if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for ``customer_id``, or ``None`` if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
