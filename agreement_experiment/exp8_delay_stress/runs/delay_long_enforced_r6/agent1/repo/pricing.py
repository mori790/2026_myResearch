"""Pricing module. Owned by agent1. Provides item and customer information to the other modules.

Implements the committed decision `pricing_api` v3:
  - money: int cents (1250 = $12.50)
  - percent: percent number (10 means 10 percent; 0 means no discount)
  - lookups that find nothing return None (item_exists returns bool,
    customer_discount_pct returns 0 for an unknown customer)

Data files are in data_pricing/ next to this file:
  catalog.csv   : sku,name,price_cents,category
  customers.csv : id,name,discount_pct,region
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pricing")


def _load_catalog(path):
    items = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            items[sku] = {
                "name": row["name"].strip(),
                "unit_price_cents": int(row["price_cents"].strip()),
                "category": row["category"].strip(),
            }
    return items


def _load_customers(path):
    customers = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["id"].strip()
            customers[cid] = {
                "name": row["name"].strip(),
                "discount_pct": int(row["discount_pct"].strip()),
                "region": row["region"].strip(),
            }
    return customers


_ITEMS = _load_catalog(os.path.join(_DATA_DIR, "catalog.csv"))
_CUSTOMERS = _load_customers(os.path.join(_DATA_DIR, "customers.csv"))


def item_exists(sku):
    """Return True if sku is in the catalog, False otherwise."""
    return sku in _ITEMS


def unit_price(sku):
    """Unit price in int cents, or None for an unknown sku."""
    item = _ITEMS.get(sku)
    return None if item is None else item["unit_price_cents"]


def customer_region(customer_id):
    """Region code (e.g. 'TX'), or None for an unknown customer."""
    customer = _CUSTOMERS.get(customer_id)
    return None if customer is None else customer["region"]


def customer_discount_pct(customer_id):
    """Percent number (10 means 10 percent). 0 for no discount and for an unknown customer."""
    customer = _CUSTOMERS.get(customer_id)
    return 0 if customer is None else customer["discount_pct"]


def customer_name(customer_id):
    """Customer name, or None for an unknown customer."""
    customer = _CUSTOMERS.get(customer_id)
    return None if customer is None else customer["name"]


# --- Additive helpers (not in pricing_api v3; flagged to the team) ---

def item_category(sku):
    """Category string (e.g. 'food', 'stationery'), or None for an unknown sku.
    Needed so invoice.py can pass (category, amount_cents) lines to tax.compute_tax."""
    item = _ITEMS.get(sku)
    return None if item is None else item["category"]


def item_name(sku):
    """Item name, or None for an unknown sku."""
    item = _ITEMS.get(sku)
    return None if item is None else item["name"]
