"""Pricing module. Owned by the PRICING developer (agent1).

Other modules (e.g. invoice.py) call these functions; they must not read the CSV files themselves.
"""


def price_of(sku):
    """Return the price of item `sku` from data/catalog.csv. If the sku is unknown, signal that it is unknown."""
    raise NotImplementedError


def discount_for(customer_id):
    """Return the discount of customer `customer_id` from data/customers.csv. Unknown customers get no discount."""
    raise NotImplementedError


def customer_name(customer_id):
    """Return the customer's name, or None if the customer is unknown."""
    raise NotImplementedError
