"""Pricing module. Owned by agent1.

Provides item and customer information to the other modules.
The data files are in data_pricing/ next to this file.

Committed team API (decision log: pricing_api, money_unit, percent_unit,
lookup_missing, region_format):

    get_item(sku)                  -> dict or None
        {"sku": str, "name": str, "price": float (dollars),
         "category": str}           # category: "stationery", "bags", "food"

    get_customer(customer_id)      -> dict or None
        {"id": str, "name": str, "discount": float (fraction, 0.10 = 10%),
         "region": str}             # region: 2-letter uppercase US state code

Money is a float in dollars (12.5 means $12.50).
Percentages are fractions (10% is 0.10).
A lookup that finds nothing returns None.
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
                # catalog.csv stores integer cents; the team uses float dollars.
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
                # customers.csv stores whole percents; the team uses fractions.
                "discount": int(row["discount_pct"]) / 100,
                "region": row["region"].strip().upper(),
            }
    return customers


_ITEMS = _load_items(_DATA_DIR / "catalog.csv")
_CUSTOMERS = _load_customers(_DATA_DIR / "customers.csv")


def get_item(sku):
    """Return item info for `sku` as a new dict, or None if unknown."""
    item = _ITEMS.get(sku)
    return None if item is None else dict(item)


def get_customer(customer_id):
    """Return customer info for `customer_id` as a new dict, or None if unknown."""
    customer = _CUSTOMERS.get(customer_id)
    return None if customer is None else dict(customer)
