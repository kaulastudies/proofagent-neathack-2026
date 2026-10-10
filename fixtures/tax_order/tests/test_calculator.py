import unittest
from calculator import calculate_total

class Acceptance(unittest.TestCase):
    def test_discount_before_tax(self):
        self.assertAlmostEqual(calculate_total(100, 20, .1), 88)
    def test_no_discount(self):
        self.assertAlmostEqual(calculate_total(100, 0, .1), 110)
    def test_full_discount(self):
        self.assertEqual(calculate_total(100, 100, .1), 0)
    def test_zero_tax(self):
        self.assertEqual(calculate_total(100, 20, 0), 80)
