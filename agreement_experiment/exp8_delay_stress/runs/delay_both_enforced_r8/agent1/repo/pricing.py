"""Item and customer information for the invoicing package.

Committed team API (decision ``pricing_api`` v1):

* ``get_item(sku)``           -> dict {sku, name, unit_price, category} or None
* ``get_customer(customer_id)`` -> dict {id, name, discount_rate, region} or None

Team conventions:

* Money is a float in dollars (1250 cents -> 12.5).
* Percentages are fractions (10% -> 0.10).
* A lookup that finds nothing returns None.

The raw data lives in ``data_pricing/`` next to this file. Prices are stored
there as integer cents and discounts as integer percents; they are converted
at load time so that nothing outside this module sees those units.

This module does not compute tax or totals.
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
                # integer cents -> float dollars
                "unit_price": int(row["price_cents"]) / 100,
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
                # integer percent -> fraction (10 -> 0.10)
                "discount_rate": int(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return item info for ``sku``, or None if the SKU is unknown.

    Returns a fresh copy, so callers cannot modify the stored data.
    """
    item = _ITEMS.get(str(sku).strip())
    if item is None:
        return None
    return dict(item)


def get_customer(customer_id):
    """Return customer info for ``customer_id``, or None if unknown.

    ``discount_rate`` is a fraction (0.10 means 10% off). Returns a fresh copy.
    """
    customer = _CUSTOMERS.get(str(customer_id).strip())
    if customer is None:
        return None
    return dict(customer)
