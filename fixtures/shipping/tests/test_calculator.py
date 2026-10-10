import unittest
from calculator import calculate_total

class Acceptance(unittest.TestCase):
    def test_discount_once(self):
        self.assertEqual(calculate_total(100, 20, 5), 85)
    def test_shipping_retained(self):
        self.assertEqual(calculate_total(100, 100, 5), 5)
    def test_free_shipping(self):
        self.assertEqual(calculate_total(100, 20, 0), 80)
    def test_no_discount(self):
        self.assertEqual(calculate_total(100, 0, 5), 105)
