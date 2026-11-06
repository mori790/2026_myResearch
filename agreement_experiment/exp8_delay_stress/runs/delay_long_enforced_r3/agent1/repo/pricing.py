"""Item and customer pricing data for the invoicing package.

Implements the committed shared decision ``pricing_api`` (v2):

* Money is a float in dollars (1250 cents -> 12.5).
* Percentages are fractions (10% -> 0.10).
* ``get_item(sku)`` returns a dict ``{sku, name, price, category}`` or None.
* ``get_customer(customer_id)`` returns a dict
  ``{id, name, discount, region}`` or None.

Data is loaded from ``data_pricing/catalog.csv`` and
``data_pricing/customers.csv``, located relative to this file.
"""

import csv
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "data_pricing"


def _load_items(path):
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
            cid = row["id"].strip()
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                # Source stores whole percent; convert to fraction (10 -> 0.10).
                "discount": int(row["discount_pct"]) / 100,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_DATA_DIR / "catalog.csv")
_CUSTOMERS = _load_customers(_DATA_DIR / "customers.csv")


def get_item(sku):
    """Return a copy of the item record for ``sku``, or None if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for ``customer_id``, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
