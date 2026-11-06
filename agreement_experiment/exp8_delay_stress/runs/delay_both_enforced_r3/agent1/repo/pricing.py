"""Item and customer information for the invoicing package.

Owned by agent1 (pricing). Data files live in ``data_pricing/`` next to this
module and are loaded relative to this file's location.

Agreed API (decision ``pricing_api`` v2 in the shared agreement log):

- ``get_item(sku)`` -> ``{"sku", "name", "price_cents", "category"}`` or ``None``
- ``get_customer(customer_id)`` -> ``{"id", "name", "discount_pct", "region"}`` or ``None``
- ``all_skus()`` -> ``list[str]``

Units: money is int cents (1250 = $12.50); percentages are percent numbers
(10 = 10%). A lookup that finds nothing returns ``None``.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _parse_number(text):
    """Return an int when the text is a whole number, otherwise a float."""
    value = float(text)
    return int(value) if value.is_integer() else value


def _load_catalog(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate sku in catalog: {sku!r}")
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "price_cents": int(row["price_cents"]),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id: {cid!r}")
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_pct": _parse_number(row["discount_pct"]),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return a copy of the item record for ``sku``, or ``None`` if unknown."""
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return a copy of the customer record for ``customer_id``, or ``None`` if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None


def all_skus():
    """Return the list of all SKUs in the catalog, in file order."""
    return list(_ITEMS.keys())
