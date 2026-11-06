"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Agreed API (decision topic ``pricing_api`` v2, committed):

* All money is an ``int`` number of cents. Never floats.
* ``get_item(sku)`` returns ``{"sku", "name", "unit_price_cents", "category"}``
  or ``None`` if the SKU is unknown.
* ``get_customer(customer_id)`` returns ``{"id", "name", "discount_percent", "region"}``
  or ``None`` if the customer is unknown. ``discount_percent`` is a decimal
  string such as ``"10"`` (exactly as in the data). ``region`` is a state code
  such as ``"TX"``.
* Discount arithmetic is NOT done here; invoice.py does it with Decimal.
* This module imports nothing from tax.py or invoice.py.
"""

import csv
import os
from decimal import Decimal, InvalidOperation

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")
_CATALOG_PATH = os.path.join(_DATA_DIR, "catalog.csv")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.csv")


def _load_items(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if sku in items:
                raise ValueError(f"duplicate sku in {path}: {sku!r}")
            items[sku] = {
                "sku": sku,
                "name": row["name"].strip(),
                "unit_price_cents": int(row["price_cents"]),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            if cid in customers:
                raise ValueError(f"duplicate customer id in {path}: {cid!r}")
            percent = row["discount_pct"].strip()
            try:
                value = Decimal(percent)
            except InvalidOperation as exc:
                raise ValueError(f"bad discount_pct for {cid!r}: {percent!r}") from exc
            if not (Decimal(0) <= value <= Decimal(100)):
                raise ValueError(f"discount_pct out of range for {cid!r}: {percent!r}")
            customers[cid] = {
                "id": cid,
                "name": row["name"].strip(),
                "discount_percent": percent,
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_items(_CATALOG_PATH)
_CUSTOMERS = _load_customers(_CUSTOMERS_PATH)


def get_item(sku):
    """Return the item for ``sku`` as a dict, or ``None`` if the SKU is unknown.

    The returned dict is a copy; changing it does not affect the catalog.
    """
    item = _ITEMS.get(sku)
    return dict(item) if item is not None else None


def get_customer(customer_id):
    """Return the customer for ``customer_id`` as a dict, or ``None`` if unknown.

    The returned dict is a copy; changing it does not affect the customer table.
    """
    customer = _CUSTOMERS.get(customer_id)
    return dict(customer) if customer is not None else None
