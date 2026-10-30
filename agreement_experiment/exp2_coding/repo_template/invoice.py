"""Invoice rendering. Owned by the INVOICE developer (agent2).

Must obtain every price, discount and customer name through the pricing module.
"""
import pricing  # noqa: F401


def render_invoice(order):
    """order = {"customer": "C1", "lines": [["A", 2], ["Z", 1]]} -> invoice text (see task description)."""
    raise NotImplementedError
