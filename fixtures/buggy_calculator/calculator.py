"""Minimal bug-reproduction example for an order total calculation."""


def calculate_total(prices, discount=0):
    subtotal = sum(prices)
    # Bug: discount is subtracted here and then again in the return expression.
    return (subtotal - discount) - discount
