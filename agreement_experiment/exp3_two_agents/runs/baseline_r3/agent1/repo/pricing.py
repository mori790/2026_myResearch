"""Pricing module. Owned by agent1 (the pricing developer).

invoice.py (written by agent2) imports this module to get everything it needs
about items and customers. The data files are in data/ next to this file.

Public API:
    get_item(sku)           -> {"sku", "name", "price_cents"}   (int cents)
    get_customer(cust_id)   -> {"id", "name", "discount_pct", "region"}
    get_tax_pct(region)     -> float (0.0 if the region has no tax row)

Unknown SKUs and customer IDs raise KeyError. Money is kept in integer cents.
"""

import csv
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _read_rows(filename):
    path = os.path.join(_DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()}
                for row in csv.DictReader(f)]


def _load_items():
    items = {}
    for row in _read_rows("catalog.csv"):
        sku = row["sku"]
        items[sku] = {
            "sku": sku,
            "name": row["name"],
            "price_cents": int(row["price_cents"]),
        }
    return items


def _load_customers():
    customers = {}
    for row in _read_rows("customers.csv"):
        cust_id = row["id"]
        customers[cust_id] = {
            "id": cust_id,
            "name": row["name"],
            "discount_pct": float(row["discount_pct"]),
            "region": row["region"],
        }
    return customers


def _load_tax():
    rates = {}
    for row in _read_rows("tax.csv"):
        rates[row["region"]] = float(row["tax_pct"])
    return rates


_ITEMS = _load_items()
_CUSTOMERS = _load_customers()
_TAX = _load_tax()


def get_item(sku):
    """Return the catalog entry for sku. Raises KeyError if unknown."""
    return dict(_ITEMS[sku])


def get_customer(cust_id):
    """Return the customer record for cust_id. Raises KeyError if unknown."""
    return dict(_CUSTOMERS[cust_id])


def get_tax_pct(region):
    """Return the tax rate in percent for region, or 0.0 if none is listed."""
    return _TAX.get(region, 0.0)
