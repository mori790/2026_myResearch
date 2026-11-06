"""Item and customer information for the invoicing package.

Conventions (committed team decision PRICING_API v1):
  * money is a float in dollars (12.5 means $12.50)
  * percentages are fractions (0.10 means 10%)
  * a lookup that finds nothing returns None

Data is read from data_pricing/catalog.csv and data_pricing/customers.csv,
located relative to this module file. The CSV files store prices in integer
cents and discounts as whole percentages; they are converted here at the
module boundary.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")

_items = None
_customers = None


def _load_items():
    global _items
    if _items is None:
        items = {}
        with open(_CATALOG_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sku = row["sku"].strip()
                items[sku] = {
                    "sku": sku,
                    "name": row["name"].strip(),
                    # CSV stores integer cents; convert to float dollars.
                    "unit_price": int(row["price_cents"].strip()) / 100,
                    "category": row["category"].strip(),
                }
        _items = items
    return _items


def _load_customers():
    global _customers
    if _customers is None:
        customers = {}
        with open(_CUSTOMERS_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = row["id"].strip()
                customers[cid] = {
                    "id": cid,
                    "name": row["name"].strip(),
                    # CSV stores whole percentages; convert to a fraction.
                    "discount": int(row["discount_pct"].strip()) / 100,
                    "region": row["region"].strip(),
                }
        _customers = customers
    return _customers


def get_item(sku):
    """Return the item for `sku` as a dict, or None if there is no such item.

    Keys: sku (str), name (str), unit_price (float dollars), category (str).
    """
    item = _load_items().get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer for `customer_id` as a dict, or None if unknown.

    Keys: id (str), name (str), discount (fraction, 0.10 = 10%),
    region (str, e.g. 'TX').
    """
    customer = _load_customers().get(customer_id)
    return dict(customer) if customer is not None else None
